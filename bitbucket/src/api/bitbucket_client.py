"""
Cliente principal de la API de Bitbucket

Implementa todas las operaciones necesarias para obtener datos de:
- Workspaces
- Projects  
- Repositories
- Commits
- Pull Requests
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


class BitbucketClient:
    """
    Cliente robusto para la API de Bitbucket
    
    Características:
    - Autenticación HTTP Basic
    - Rate limiting inteligente
    - Manejo de errores y reintentos
    - Paginación automática
    - Logging detallado
    """
    
    def __init__(self):
        """Inicializar cliente de Bitbucket"""
        self.settings = get_settings()
        
        # Configuración de autenticación
        self.auth = HTTPBasicAuth(
            self.settings.bitbucket_username,
            self.settings.bitbucket_app_password
        )
        
        # Configuración de HTTP
        self.base_url = self.settings.api_base_url
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
            'User-Agent': 'Bitbucket-DevOps-Metrics/1.0.0'
        }
        
        logger.info(f"Cliente de Bitbucket inicializado - Base URL: {self.base_url}, Username: {self.settings.bitbucket_username}, Rate Limit: {self.settings.api_rate_limit}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realizar request HTTP a la API de Bitbucket
        
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
        # Construir URL completa manteniendo la base URL
        if self.base_url.endswith('/'):
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.base_url}/{endpoint}"
        
        # Agregar parámetros de query si existen
        if params:
            url += f"?{urlencode(params)}"
        
        logger.debug(f"Realizando request HTTP - Method: {method}, URL: {url}, Params: {params}")
        
        async def _http_request():
            async with httpx.AsyncClient(
                timeout=self.timeout,
                auth=self.auth,
                headers=self.default_headers
            ) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data if data else None
                )
                
                # Verificar status code
                response.raise_for_status()
                
                # Actualizar información de rate limiting
                self.rate_limiter._update_rate_limit_info(dict(response.headers))
                
                return response.json()
        
        # Ejecutar con rate limiting
        return await self.rate_limiter.execute_with_rate_limit(_http_request)
    
    async def get_workspace(self, workspace_slug: str) -> Dict[str, Any]:
        """
        Obtener información de un workspace específico
        
        Args:
            workspace_slug: Slug del workspace
            
        Returns:
            Información del workspace
        """
        endpoint = f"workspaces/{workspace_slug}"
        
        logger.info(f"Obteniendo información del workspace: {workspace_slug}")
        
        try:
            response = await self._make_request("GET", endpoint)
            logger.info(f"Workspace obtenido exitosamente: {workspace_slug}, Nombre: {response.get('name')}")
            return response
        except Exception as e:
            logger.error(f"Error al obtener workspace {workspace_slug}: {str(e)}")
            raise
    
    async def get_project(self, workspace_slug: str, project_key: str) -> Dict[str, Any]:
        """
        Obtener información de un proyecto específico
        
        Args:
            workspace_slug: Slug del workspace
            project_key: Clave del proyecto
            
        Returns:
            Información del proyecto
        """
        endpoint = f"workspaces/{workspace_slug}/projects/{project_key}"
        
        logger.info(f"Obteniendo información del proyecto {workspace_slug}/{project_key}")
        
        try:
            response = await self._make_request("GET", endpoint)
            logger.info(f"Proyecto obtenido exitosamente: {workspace_slug}/{project_key}, Nombre: {response.get('name')}")
            return response
        except Exception as e:
            logger.error(f"Error al obtener proyecto {workspace_slug}/{project_key}: {str(e)}")
            raise
    
    async def get_workspace_projects(
        self,
        workspace_slug: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener proyectos de un workspace
        
        Args:
            workspace_slug: Slug del workspace
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Lista de proyectos
        """
        endpoint = f"workspaces/{workspace_slug}/projects"
        params = {
            'page': page,
            'pagelen': page_size
        }
        
        logger.info(
            f"Obteniendo proyectos del workspace: {workspace_slug}, Page: {page}, Page Size: {page_size}"
        )
        
        try:
            response = await self._make_request("GET", endpoint, params=params)
            projects = response.get('values', [])
            
            logger.info(f"Proyectos obtenidos exitosamente - Workspace: {workspace_slug}, Total: {len(projects)}, Page: {page}")
            
            return projects
        except Exception as e:
            logger.error(f"Error al obtener proyectos del workspace - Workspace: {workspace_slug}, Page: {page}, Error: {str(e)}")
            raise
    
    async def get_all_workspace_projects(self, workspace_slug: str) -> List[Dict[str, Any]]:
        """
        Obtener todos los proyectos de un workspace (con paginación automática)
        
        Args:
            workspace_slug: Slug del workspace
            
        Returns:
            Lista completa de proyectos
        """
        all_projects = []
        page = 1
        page_size = 100
        
        logger.info(f"Obteniendo todos los proyectos del workspace: {workspace_slug}")
        
        while True:
            try:
                projects = await self.get_workspace_projects(
                    workspace_slug, page, page_size
                )
                
                if not projects:
                    break
                
                all_projects.extend(projects)
                page += 1
                
                # Si obtenemos menos proyectos que el tamaño de página, es la última
                if len(projects) < page_size:
                    break
                    
            except Exception as e:
                logger.error(f"Error al obtener página de proyectos - Workspace: {workspace_slug}, Page: {page}, Error: {str(e)}")
                raise
        
        logger.info(f"Todos los proyectos obtenidos exitosamente - Workspace: {workspace_slug}, Total: {len(all_projects)}")
        
        return all_projects
    
    async def get_workspace_repositories(
        self,
        workspace_slug: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener repositorios de un workspace
        
        Args:
            workspace_slug: Slug del workspace
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Lista de repositorios
        """
        endpoint = f"repositories/{workspace_slug}"
        params = {
            'page': page,
            'pagelen': page_size
        }
        
        logger.info(
            f"Obteniendo repositorios del workspace: {workspace_slug}, Page: {page}, Page Size: {page_size}"
        )
        
        try:
            response = await self._make_request("GET", endpoint, params=params)
            repositories = response.get('values', [])
            
            logger.info(
                f"Repositorios obtenidos exitosamente - Workspace: {workspace_slug}, Total: {len(repositories)}, Page: {page}"
            )
            
            return repositories
        except Exception as e:
            logger.error(
                f"Error al obtener repositorios del workspace - Workspace: {workspace_slug}, Page: {page}, Error: {str(e)}"
            )
            raise
    
    async def get_all_workspace_repositories(self, workspace_slug: str) -> List[Dict[str, Any]]:
        """
        Obtener todos los repositorios de un workspace (con paginación automática)
        
        Args:
            workspace_slug: Slug del workspace
            
        Returns:
            Lista completa de repositorios
        """
        all_repositories = []
        page = 1
        page_size = 100
        
        logger.info(
            f"Obteniendo todos los repositorios del workspace: {workspace_slug}"
        )
        
        while True:
            try:
                repositories = await self.get_workspace_repositories(
                    workspace_slug, page, page_size
                )
                
                if not repositories:
                    break
                
                all_repositories.extend(repositories)
                page += 1
                
                # Si obtenemos menos repositorios que el tamaño de página, es la última
                if len(repositories) < page_size:
                    break
                    
            except Exception as e:
                logger.error(
                    f"Error al obtener página de repositorios - Workspace: {workspace_slug}, Page: {page}, Error: {str(e)}"
                )
                raise
        
        logger.info(
            f"Todos los repositorios obtenidos exitosamente - Workspace: {workspace_slug}, Total: {len(all_repositories)}"
        )
        
        return all_repositories
    
    async def get_project_repositories(
        self,
        workspace_slug: str,
        project_key: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener repositorios de un proyecto específico
        
        Args:
            workspace_slug: Slug del workspace
            project_key: Clave del proyecto
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Lista de repositorios del proyecto
        """
        endpoint = f"repositories/{workspace_slug}"
        params = {
            'q': f'project.key="{project_key}"',
            'page': page,
            'pagelen': page_size
        }
        
        logger.info(
            f"Obteniendo repositorios del proyecto - Workspace: {workspace_slug}, Project: {project_key}, Page: {page}, Page Size: {page_size}"
        )
        
        try:
            response = await self._make_request("GET", endpoint, params=params)
            repositories = response.get('values', [])
            
            logger.info(
                f"Repositorios del proyecto obtenidos exitosamente - Workspace: {workspace_slug}, Project: {project_key}, Total: {len(repositories)}, Page: {page}"
            )
            
            return repositories
        except Exception as e:
            logger.error(
                f"Error al obtener repositorios del proyecto - Workspace: {workspace_slug}, Project: {project_key}, Page: {page}, Error: {str(e)}"
            )
            raise
    
    async def get_all_project_repositories(
        self,
        workspace_slug: str,
        project_key: str
    ) -> List[Dict[str, Any]]:
        """
        Obtener todos los repositorios de un proyecto (con paginación automática)
        
        Args:
            workspace_slug: Slug del workspace
            project_key: Clave del proyecto
            
        Returns:
            Lista completa de repositorios del proyecto
        """
        all_repositories = []
        page = 1
        page_size = 100
        
        logger.info(
            f"Obteniendo todos los repositorios del proyecto - Workspace: {workspace_slug}, Project: {project_key}"
        )
        
        while True:
            try:
                repositories = await self.get_project_repositories(
                    workspace_slug, project_key, page, page_size
                )
                
                if not repositories:
                    break
                
                all_repositories.extend(repositories)
                page += 1
                
                # Si obtenemos menos repositorios que el tamaño de página, es la última
                if len(repositories) < page_size:
                    break
                    
            except Exception as e:
                logger.error(
                    f"Error al obtener página de repositorios del proyecto - Workspace: {workspace_slug}, Project: {project_key}, Page: {page}, Error: {str(e)}"
                )
                raise
        
        logger.info(
            f"Todos los repositorios del proyecto obtenidos exitosamente - Workspace: {workspace_slug}, Project: {project_key}, Total: {len(all_repositories)}"
        )
        
        return all_repositories
    
    async def get_repository(
        self,
        workspace_slug: str,
        repository_slug: str
    ) -> Dict[str, Any]:
        """
        Obtener información detallada de un repositorio específico
        
        Args:
            workspace_slug: Slug del workspace
            repository_slug: Slug del repositorio
            
        Returns:
            Información detallada del repositorio
        """
        endpoint = f"repositories/{workspace_slug}/{repository_slug}"
        
        logger.info(f"Obteniendo información del repositorio {workspace_slug}/{repository_slug}")
        
        try:
            response = await self._make_request("GET", endpoint)
            
            logger.info(f"Repositorio obtenido exitosamente: {workspace_slug}/{repository_slug}, Nombre: {response.get('name')}")
            
            return response
        except Exception as e:
            logger.error(f"Error al obtener repositorio {workspace_slug}/{repository_slug}: {str(e)}")
            raise
    
    async def get_repository_commits(
        self,
        workspace_slug: str,
        repository_slug: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener commits de un repositorio
        
        Args:
            workspace_slug: Slug del workspace
            repository_slug: Slug del repositorio
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Lista de commits
        """
        endpoint = f"repositories/{workspace_slug}/{repository_slug}/commits"
        params = {
            'page': page,
            'pagelen': page_size
        }
        
        logger.info(
            f"Obteniendo commits del repositorio - Workspace: {workspace_slug}, Repository: {repository_slug}, Page: {page}, Page Size: {page_size}"
        )
        
        try:
            response = await self._make_request("GET", endpoint, params=params)
            commits = response.get('values', [])
            
            logger.info(
                f"Commits obtenidos exitosamente - Workspace: {workspace_slug}, Repository: {repository_slug}, Total: {len(commits)}, Page: {page}"
            )
            
            return commits
        except Exception as e:
            logger.error(
                f"Error al obtener commits del repositorio - Workspace: {workspace_slug}, Repository: {repository_slug}, Page: {page}, Error: {str(e)}"
            )
            raise
    
    async def get_repository_pull_requests(
        self,
        workspace_slug: str,
        repository_slug: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener pull requests de un repositorio
        
        Args:
            workspace_slug: Slug del workspace
            repository_slug: Slug del repositorio
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Lista de pull requests
        """
        endpoint = f"repositories/{workspace_slug}/{repository_slug}/pullrequests"
        params = {
            'page': page,
            'pagelen': page_size
        }
        
        logger.info(
            f"Obteniendo pull requests del repositorio - Workspace: {workspace_slug}, Repository: {repository_slug}, Page: {page}, Page Size: {page_size}"
        )
        
        try:
            response = await self._make_request("GET", endpoint, params=params)
            pull_requests = response.get('values', [])
            
            logger.info(
                f"Pull requests obtenidos exitosamente - Workspace: {workspace_slug}, Repository: {repository_slug}, Total: {len(pull_requests)}, Page: {page}"
            )
            
            return pull_requests
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.warning(
                    f"Pull requests no disponibles para el repositorio - Workspace: {workspace_slug}, Repository: {repository_slug}, Error: {str(e)}"
                )
                return []  # Retornar lista vacía en lugar de fallar
            else:
                logger.error(
                    f"Error al obtener pull requests del repositorio - Workspace: {workspace_slug}, Repository: {repository_slug}, Page: {page}, Error: {str(e)}"
                )
                raise
        except Exception as e:
            logger.error(
                f"Error al obtener pull requests del repositorio - Workspace: {workspace_slug}, Repository: {repository_slug}, Page: {page}, Error: {str(e)}"
            )
            raise
    
    def get_rate_limiter_status(self) -> Dict[str, Any]:
        """
        Obtener estado del rate limiter
        
        Returns:
            Estado del rate limiter
        """
        return self.rate_limiter.get_status()
    
    async def close(self):
        """Cerrar cliente y liberar recursos"""
        logger.info("Cerrando cliente de Bitbucket")
        # No hay recursos específicos que cerrar en httpx
