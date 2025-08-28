"""
Rate Limiter para SonarCloud API

Implementa control de velocidad de requests para evitar
exceder los límites de la API de SonarCloud.
"""

import asyncio
import time
from typing import Any, Callable, Optional
from datetime import datetime, timedelta

from ..config.settings import get_settings
from ..utils.logger import get_logger


class RateLimiter:
    """
    Controlador de velocidad de requests para SonarCloud API
    
    Implementa rate limiting con backoff exponencial y reintentos
    automáticos para manejar errores de la API.
    """
    
    def __init__(
        self,
        max_requests: int = 1000,
        time_window: int = 3600,
        retry_attempts: int = 1
    ):
        """
        Inicializar rate limiter
        
        Args:
            max_requests: Máximo número de requests en el período
            time_window: Ventana de tiempo en segundos
            retry_attempts: Número de intentos de reintento
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.retry_attempts = retry_attempts
        self.logger = get_logger(__name__)
        
        # Historial de requests
        self.request_times = []
        
        # Configuración de backoff
        self.base_delay = 1.0
        self.max_delay = 60.0
        
        self.logger.debug(
            "Rate limiter inicializado",
            max_requests=max_requests,
            time_window=time_window,
            retry_attempts=retry_attempts
        )
    
    def _clean_old_requests(self) -> None:
        """Limpiar requests antiguos del historial"""
        current_time = time.time()
        cutoff_time = current_time - self.time_window
        
        # Mantener solo requests dentro de la ventana de tiempo
        self.request_times = [req_time for req_time in self.request_times if req_time > cutoff_time]
    
    def _can_make_request(self) -> bool:
        """
        Verificar si se puede hacer un request
        
        Returns:
            bool: True si se puede hacer request
        """
        self._clean_old_requests()
        return len(self.request_times) < self.max_requests
    
    def _wait_if_needed(self) -> None:
        """Esperar si es necesario para respetar el rate limit"""
        if not self._can_make_request():
            # Calcular tiempo de espera
            oldest_request = min(self.request_times)
            wait_time = self.time_window - (time.time() - oldest_request)
            
            if wait_time > 0:
                self.logger.info(f"Rate limit alcanzado, esperando {wait_time:.2f} segundos")
                time.sleep(wait_time)
    
    def _record_request(self) -> None:
        """Registrar un request en el historial"""
        self.request_times.append(time.time())
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """
        Calcular delay para backoff exponencial
        
        Args:
            attempt: Número de intento
            
        Returns:
            float: Delay en segundos
        """
        delay = self.base_delay * (2 ** (attempt - 1))
        return min(delay, self.max_delay)
    
    async def execute_request(
        self,
        request_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Ejecutar request con rate limiting y reintentos
        
        Args:
            request_func: Función de request a ejecutar
            *args: Argumentos posicionales para la función
            **kwargs: Argumentos nombrados para la función
            
        Returns:
            Resultado del request
            
        Raises:
            Exception: Si todos los reintentos fallan
        """
        for attempt in range(1, self.retry_attempts + 2):  # +2 para incluir el intento inicial
            try:
                # Esperar si es necesario para respetar rate limit
                self._wait_if_needed()
                
                # Registrar request
                self._record_request()
                
                # Ejecutar request
                self.logger.debug(f"Ejecutando request - Attempt: {attempt}")
                
                if asyncio.iscoroutinefunction(request_func):
                    response = await request_func(*args, **kwargs)
                else:
                    response = request_func(*args, **kwargs)
                
                self.logger.debug(f"Request exitoso - Attempt: {attempt}")
                return response
                
            except Exception as e:
                self.logger.warning(
                    f"Error en request - Attempt: {attempt}, Error: {str(e)}"
                )
                
                # Si es el último intento, re-raise la excepción
                if attempt == self.retry_attempts + 1:
                    self.logger.error(f"Todos los intentos fallaron - Error: {str(e)}")
                    raise
                
                # Calcular delay para reintento
                delay = self._calculate_backoff_delay(attempt)
                self.logger.info(f"Esperando antes de reintentar - Wait time: {delay}, Attempt: {attempt}")
                
                # Esperar antes del reintento
                await asyncio.sleep(delay)
    
    def get_stats(self) -> dict:
        """
        Obtener estadísticas del rate limiter
        
        Returns:
            dict: Estadísticas del rate limiter
        """
        self._clean_old_requests()
        
        return {
            'max_requests': self.max_requests,
            'time_window': self.time_window,
            'current_requests': len(self.request_times),
            'remaining_requests': max(0, self.max_requests - len(self.request_times)),
            'retry_attempts': self.retry_attempts
        }
    
    def reset(self) -> None:
        """Resetear el historial de requests"""
        self.request_times.clear()
        self.logger.info("Rate limiter reseteado")
