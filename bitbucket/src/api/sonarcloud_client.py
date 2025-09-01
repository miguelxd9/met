"""
Cliente principal de la API de SonarCloud

Implementa todas las operaciones necesarias para obtener datos de:
- Organizations
- Projects
- Issues
- Security Hotspots
- Quality Gates
- Metrics
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlencode
import httpx
from requests.auth import HTTPBasicAuth

from src.config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.rate_limiter import RateLimiter

logger = get_logger(__name__)


class SonarCloudClient:
    """
    Cliente robusto para la API de SonarCloud
    
    Características:
    - Autenticación HTTP Basic
    - Rate limiting inteligente
    - Manejo de errores y reintentos
    - Paginación automática
    - Logging detallado
    """
    
    def __init__(self):
        """Inicializar cliente de SonarCloud"""
        self.settings = get_settings()
        
        # Configuración de autenticación
        self.auth = HTTPBasicAuth(
            self.settings.sonarcloud_token,
            ''  # SonarCloud usa token como username
        )
        
        # Configuración de HTTP
        self.base_url = self.settings.sonarcloud_api_base_url
        self.timeout = self.settings.api_timeout
        self.retry_attempts = self.settings.api_retry_attempts
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_requests_per_hour=self.settings.api_rate_limit,
            burst_limit=10,
            retry_attempts=self.retry_attempts
        )
        
        # Headers por defecto
        self.default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'SonarCloud-DevOps-Metrics/1.0.0'
        }
        
        logger.info(f"Cliente de SonarCloud inicializado - Base URL: {self.base_url}, Rate Limit: {self.settings.api_rate_limit}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realizar request HTTP a la API de SonarCloud
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint de la API
            params: Parámetros de query
            data: Datos del body
            
        Returns:
            Respuesta de la API como diccionario
            
        Raises:
            Exception: Si el request falla
        """
        # Construir URL completa
        if self.base_url.endswith('/'):
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.base_url}/{endpoint}"
        
        # Agregar parámetros de query si existen
        if params:
            url += f"?{urlencode(params)}"
        
        # Aplicar rate limiting
        self.rate_limiter._wait_if_needed()
        
        # Configurar cliente HTTP
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.default_headers
        ) as client:
            
            # Realizar request
            try:
                if method.upper() == 'GET':
                    response = await client.get(url, auth=self.auth)
                elif method.upper() == 'POST':
                    response = await client.post(url, auth=self.auth, json=data)
                elif method.upper() == 'PUT':
                    response = await client.put(url, auth=self.auth, json=data)
                elif method.upper() == 'DELETE':
                    response = await client.delete(url, auth=self.auth)
                else:
                    raise ValueError(f"Método HTTP no soportado: {method}")
                
                # Verificar respuesta
                response.raise_for_status()
                
                # Log del request exitoso
                logger.debug(f"Request exitoso - {method} {url} - Status: {response.status_code}")
                
                # Retornar respuesta JSON
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Error HTTP en request - {method} {url} - Status: {e.response.status_code} - Response: {e.response.text}")
                raise Exception(f"Error HTTP {e.response.status_code}: {e.response.text}")
                
            except httpx.RequestError as e:
                logger.error(f"Error de conexión en request - {method} {url} - Error: {str(e)}")
                raise Exception(f"Error de conexión: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error inesperado en request - {method} {url} - Error: {str(e)}")
                raise
    
    async def get_organization(self, organization_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de una organización
        
        Args:
            organization_key: Clave de la organización
            
        Returns:
            Información de la organización o None si no se encuentra
        """
        logger.info(f"Obteniendo información de la organización: {organization_key}")
        
        try:
            # SonarCloud no tiene endpoint específico para organizaciones
            # Vamos a verificar la organización obteniendo proyectos
            endpoint = f"projects/search"
            params = {
                'organization': organization_key,
                'ps': 1  # Solo 1 proyecto para verificar que la organización existe
            }
            
            response = await self._make_request('GET', endpoint, params=params)
            
            # Si obtenemos respuesta, la organización existe
            organization_info = {
                'key': organization_key,
                'name': organization_key,  # Usar la clave como nombre por defecto
                'total_projects': response.get('paging', {}).get('total', 0)
            }
            
            logger.info(f"Organización verificada exitosamente: {organization_key}, Total proyectos: {organization_info['total_projects']}")
            return organization_info
            
        except Exception as e:
            logger.error(f"Error al obtener organización - Organization: {organization_key}, Error: {str(e)}")
            return None
    
    async def get_organization_projects(
        self,
        organization_key: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener proyectos de una organización
        
        Args:
            organization_key: Clave de la organización
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Lista de proyectos
        """
        logger.info(f"Obteniendo proyectos de la organización - Organization: {organization_key}, Page: {page}, Page Size: {page_size}")
        
        try:
            endpoint = f"projects/search"
            params = {
                'organization': organization_key,
                'p': page,
                'ps': page_size
            }
            
            response = await self._make_request('GET', endpoint, params=params)
            
            projects = response.get('components', [])
            logger.info(f"Proyectos obtenidos exitosamente - Organization: {organization_key}, Total: {len(projects)}, Page: {page}")
            

            
            return projects
            
        except Exception as e:
            logger.error(f"Error al obtener proyectos de la organización - Organization: {organization_key}, Page: {page}, Error: {str(e)}")
            return []
    
    async def get_all_organization_projects(self, organization_key: str) -> List[Dict[str, Any]]:
        """
        Obtener todos los proyectos de una organización con paginación automática
        
        Args:
            organization_key: Clave de la organización
            
        Returns:
            Lista completa de proyectos
        """
        logger.info(f"Obteniendo todos los proyectos de la organización: {organization_key}")
        
        all_projects = []
        page = 1
        page_size = 100
        
        while True:
            projects = await self.get_organization_projects(
                organization_key, page, page_size
            )
            
            if not projects:
                break
                
            all_projects.extend(projects)
            
            # Si obtenemos menos proyectos que el tamaño de página, hemos llegado al final
            if len(projects) < page_size:
                break
                
            page += 1
            
            # Pequeña pausa para no sobrecargar la API
            await asyncio.sleep(0.1)
        
        logger.info(f"Todos los proyectos obtenidos exitosamente - Organization: {organization_key}, Total: {len(all_projects)}")
        return all_projects
    
    async def get_project_issues(
        self,
        project_key: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener issues de un proyecto
        
        Args:
            project_key: Clave del proyecto
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Lista de issues
        """
        logger.info(f"Obteniendo issues del proyecto - Project: {project_key}, Page: {page}, Page Size: {page_size}")
        
        try:
            endpoint = f"issues/search"
            params = {
                'componentKeys': project_key,
                'p': page,
                'ps': page_size
            }
            
            response = await self._make_request('GET', endpoint, params=params)
            
            issues = response.get('issues', [])
            logger.info(f"Issues obtenidos exitosamente - Project: {project_key}, Total: {len(issues)}, Page: {page}")
            
            return issues
            
        except Exception as e:
            logger.error(f"Error al obtener issues del proyecto - Project: {project_key}, Page: {page}, Error: {str(e)}")
            return []
    
    async def get_project_security_hotspots(
        self,
        project_key: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener security hotspots de un proyecto
        
        Args:
            project_key: Clave del proyecto
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Lista de security hotspots
        """
        logger.info(f"Obteniendo security hotspots del proyecto - Project: {project_key}, Page: {page}, Page Size: {page_size}")
        
        try:
            endpoint = f"hotspots/search"
            params = {
                'projectKey': project_key,
                'p': page,
                'ps': page_size
            }
            
            response = await self._make_request('GET', endpoint, params=params)
            
            hotspots = response.get('hotspots', [])
            logger.info(f"Security hotspots obtenidos exitosamente - Project: {project_key}, Total: {len(hotspots)}, Page: {page}")
            
            return hotspots
            
        except Exception as e:
            logger.error(f"Error al obtener security hotspots del proyecto - Project: {project_key}, Page: {page}, Error: {str(e)}")
            return []
    
    async def get_project_quality_gate(self, project_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtener quality gate de un proyecto
        
        Args:
            project_key: Clave del proyecto
            
        Returns:
            Información del quality gate o None si no se encuentra
        """
        logger.info(f"Obteniendo quality gate del proyecto: {project_key}")
        
        try:
            endpoint = f"qualitygates/project_status"
            params = {'projectKey': project_key}
            
            response = await self._make_request('GET', endpoint, params=params)
            
            logger.info(f"Quality gate obtenido exitosamente - Project: {project_key}")
            return response
            
        except Exception as e:
            logger.error(f"Error al obtener quality gate del proyecto - Project: {project_key}, Error: {str(e)}")
            return None
    
    async def get_project_metrics(
        self,
        project_key: str,
        metrics: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener métricas de un proyecto
        
        Args:
            project_key: Clave del proyecto
            metrics: Lista de métricas a obtener (si es None, se obtienen métricas por defecto)
            
        Returns:
            Lista de métricas
        """
        logger.info(f"Obteniendo métricas del proyecto: {project_key}")
        
        try:
            endpoint = f"measures/component"
            
            # Métricas por defecto si no se especifican (usar solo las disponibles en SonarCloud)
            if metrics is None:
                metrics = [
                    'bugs', 'vulnerabilities', 'code_smells', 'security_hotspots',
                    'coverage', 'duplicated_lines_density', 'reliability_rating',
                    'security_rating', 'sqale_rating'
                ]
            
            params = {
                'component': project_key,
                'metricKeys': ','.join(metrics)
            }
            
            response = await self._make_request('GET', endpoint, params=params)
            
            measures = response.get('component', {}).get('measures', [])
            logger.info(f"Métricas obtenidas exitosamente - Project: {project_key}, Total: {len(measures)}")
            
            return measures
            
        except Exception as e:
            logger.error(f"Error al obtener métricas del proyecto - Project: {project_key}, Error: {str(e)}")
            return []
    
    async def get_project_details(self, project_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtener detalles completos de un proyecto
        
        Args:
            project_key: Clave del proyecto
            
        Returns:
            Detalles del proyecto o None si no se encuentra
        """
        logger.info(f"Obteniendo detalles del proyecto: {project_key}")
        
        try:
            # Según la documentación oficial de SonarCloud, el endpoint correcto es components/show
            endpoint = f"components/show"
            params = {'component': project_key}
            
            response = await self._make_request('GET', endpoint, params=params)
            

            
            logger.info(f"Detalles del proyecto obtenidos exitosamente - Project: {project_key}, Name: {response.get('name')}")
            return response
            
        except Exception as e:
            logger.error(f"Error al obtener detalles del proyecto - Project: {project_key}, Error: {str(e)}")
            return None
