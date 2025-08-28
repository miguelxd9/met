"""
Sistema de rate limiting para la API de Bitbucket
"""

import time
import asyncio
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitInfo:
    """Información sobre el rate limiting"""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None


class RateLimiter:
    """
    Sistema de rate limiting inteligente para la API de Bitbucket
    
    Implementa:
    - Control de requests por hora
    - Backoff exponencial
    - Cola de requests
    - Respeta headers de rate limiting de la API
    """
    
    def __init__(
        self,
        max_requests_per_hour: int = 1000, # Máximo 1000 requests por hora
        burst_limit: int = 10, # Máximo 10 requests simultáneos
        retry_attempts: int = 1
    ):
        """
        Inicializar rate limiter
        
        Args:
            max_requests_per_hour: Máximo de requests por hora
            burst_limit: Límite de requests simultáneos
            retry_attempts: Número de intentos de reintento
        """
        self.max_requests_per_hour = max_requests_per_hour
        self.burst_limit = burst_limit
        self.retry_attempts = retry_attempts
        
        # Control de requests
        self.request_times = deque(maxlen=max_requests_per_hour)
        self.current_burst = 0
        
        # Estado del rate limiting
        self.rate_limit_info: Optional[RateLimitInfo] = None
        self.last_request_time = 0
        
        # Semáforo para controlar requests simultáneos
        self.semaphore = asyncio.Semaphore(burst_limit)
        
        logger.info(f"Rate limiter inicializado - Max requests por hora: {max_requests_per_hour}, Burst limit: {burst_limit}, Retry attempts: {retry_attempts}")
    
    def _can_make_request(self) -> bool:
        """
        Verificar si se puede hacer un request
        
        Returns:
            bool: True si se puede hacer request, False en caso contrario
        """
        now = time.time()
        
        # Verificar si hay rate limiting activo de la API
        if self.rate_limit_info and self.rate_limit_info.remaining <= 0:
            if datetime.now() < self.rate_limit_info.reset_time:
                logger.warning(f"Rate limit de la API alcanzado - Reset time: {self.rate_limit_info.reset_time}, Remaining: {self.rate_limit_info.remaining}")
                return False
        
        # Verificar límite local por hora
        if len(self.request_times) >= self.max_requests_per_hour:
            oldest_request = self.request_times[0]
            if now - oldest_request < 3600:  # 1 hora
                logger.warning(f"Límite local de requests por hora alcanzado - Oldest request: {oldest_request}, Current time: {now}")
                return False
        
        # Verificar límite de burst
        if self.current_burst >= self.burst_limit:
            logger.warning(f"Límite de burst alcanzado - Current burst: {self.current_burst}, Burst limit: {self.burst_limit}")
            return False
        
        return True
    
    def _wait_if_needed(self) -> float:
        """
        Esperar si es necesario antes de hacer un request
        
        Returns:
            float: Tiempo de espera en segundos
        """
        wait_time = 0
        
        # Esperar si hay rate limiting de la API
        if self.rate_limit_info and self.rate_limit_info.retry_after:
            wait_time = max(wait_time, self.rate_limit_info.retry_after)
        
        # Esperar si se alcanzó el límite por hora
        if len(self.request_times) >= self.max_requests_per_hour:
            oldest_request = self.request_times[0]
            time_since_oldest = time.time() - oldest_request
            if time_since_oldest < 3600:
                wait_time = max(wait_time, 3600 - time_since_oldest)
        
        if wait_time > 0:
            logger.info(f"Esperando antes de hacer request - Wait time: {wait_time}, Reason: rate_limiting")
            time.sleep(wait_time)
        
        return wait_time
    
    def _update_rate_limit_info(self, headers: dict) -> None:
        """
        Actualizar información de rate limiting desde headers de respuesta
        
        Args:
            headers: Headers de respuesta de la API
        """
        try:
            # Extraer información de rate limiting de headers
            limit = int(headers.get('X-RateLimit-Limit', self.max_requests_per_hour))
            remaining = int(headers.get('X-RateLimit-Remaining', self.max_requests_per_hour))
            reset_time_str = headers.get('X-RateLimit-Reset')
            retry_after = headers.get('Retry-After')
            
            if reset_time_str:
                reset_timestamp = int(reset_time_str)
                reset_time = datetime.fromtimestamp(reset_timestamp)
            else:
                reset_time = datetime.now() + timedelta(hours=1)
            
            retry_after_int = int(retry_after) if retry_after else None
            
            self.rate_limit_info = RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=retry_after_int
            )
            
            logger.debug(f"Rate limit info actualizado - Limit: {limit}, Remaining: {remaining}, Reset time: {reset_time}, Retry after: {retry_after_int}")
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error al parsear headers de rate limiting - Error: {str(e)}, Headers: {headers}")
    
    def _record_request(self) -> None:
        """Registrar que se hizo un request"""
        now = time.time()
        self.request_times.append(now)
        self.current_burst += 1
        self.last_request_time = now
        
        logger.debug(f"Request registrado - Current burst: {self.current_burst}, Total requests: {len(self.request_times)}")
    
    def _release_burst_slot(self) -> None:
        """Liberar slot de burst"""
        self.current_burst = max(0, self.current_burst - 1)
        logger.debug(f"Slot de burst liberado - Current burst: {self.current_burst}")
    
    async def execute_with_rate_limit(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Ejecutar función con control de rate limiting
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la función
            
        Raises:
            Exception: Si se exceden los intentos de reintento
        """
        async with self.semaphore:
            for attempt in range(self.retry_attempts):
                try:
                    # Verificar si se puede hacer request
                    if not self._can_make_request():
                        self._wait_if_needed()
                    
                    # Ejecutar función
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Registrar request exitoso
                    self._record_request()
                    
                    logger.debug(f"Request ejecutado exitosamente - Attempt: {attempt + 1}, Execution time: {execution_time}")
                    
                    return result
                    
                except Exception as e:
                    logger.warning(f"Error en request - Attempt: {attempt + 1}, Error: {str(e)}, Retry attempts remaining: {self.retry_attempts - attempt - 1}")
                    
                    if attempt == self.retry_attempts - 1:
                        # Último intento fallido
                        logger.error(f"Todos los intentos de reintento fallaron - Error: {str(e)}, Total attempts: {self.retry_attempts}")
                        raise
                    
                    # Esperar antes de reintentar (backoff exponencial)
                    wait_time = min(2 ** attempt, 60)  # Máximo 60 segundos
                    logger.info(f"Esperando antes de reintentar - Wait time: {wait_time}, Attempt: {attempt + 1}")
                    await asyncio.sleep(wait_time)
                    
                finally:
                    # Siempre liberar slot de burst
                    self._release_burst_slot()
    
    def sync_execute_with_rate_limit(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Ejecutar función síncrona con control de rate limiting
        
        Args:
            func: Función síncrona a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la función
        """
        # Para funciones síncronas, usar asyncio.run
        async def async_wrapper():
            return await self.execute_with_rate_limit(func, *args, **kwargs)
        
        return asyncio.run(async_wrapper())
    
    def get_status(self) -> dict:
        """
        Obtener estado actual del rate limiter
        
        Returns:
            dict: Estado del rate limiter
        """
        return {
            'max_requests_per_hour': self.max_requests_per_hour,
            'current_requests_this_hour': len(self.request_times),
            'current_burst': self.current_burst,
            'burst_limit': self.burst_limit,
            'rate_limit_info': self.rate_limit_info.__dict__ if self.rate_limit_info else None,
            'last_request_time': self.last_request_time
        }
