"""
Cliente de API para SonarCloud

Implementa la comunicación con la API oficial de SonarCloud
para obtener métricas de calidad de código, proyectos, issues,
security hotspots y quality gates.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode

import httpx
from httpx import HTTPStatusError

from ..config.settings import get_settings
from ..utils.logger import get_logger
from ..utils.rate_limiter import RateLimiter


class SonarCloudClient:
    """
    Cliente para interactuar con la API de SonarCloud
    
    Proporciona métodos para obtener datos de proyectos, métricas,
    issues, security hotspots y quality gates con rate limiting
    y manejo de errores.
    """
    
    def __init__(self):
        """Inicializar cliente de SonarCloud"""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.rate_limiter = RateLimiter(
            max_requests=self.settings.api_rate_limit,
            time_window=3600  # 1 hora
        )
        
        # Headers de autenticación
        self.headers = {
            'Authorization': f'Bearer {self.settings.sonarcloud_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'SonarCloud-Metrics-DevOps/1.0.0'
        }
        
        self.logger.info("Cliente de SonarCloud inicializado")
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """
        Realizar request a la API de SonarCloud con rate limiting
        
        Args:
            endpoint: Endpoint de la API
            params: Parámetros de query
            method: Método HTTP
            
        Returns:
            Dict con la respuesta de la API
            
        Raises:
            HTTPStatusError: Si hay error en la respuesta
        """
        url = f"{self.settings.api_base_url}/{endpoint}"
        
        if params:
            url += f"?{urlencode(params)}"
        
        self.logger.debug(f"Realizando request - URL: {url}, Method: {method}")
        
        async with httpx.AsyncClient(timeout=self.settings.api_timeout) as client:
            response = await self.rate_limiter.execute_request(
                client.request,
                method=method,
                url=url,
                headers=self.headers
            )
            
            response.raise_for_status()
            return response.json()
    
    async def get_organization(self, organization_key: str) -> Dict[str, Any]:
        """
        Obtener información de una organización
        
        Args:
            organization_key: Clave de la organización
            
        Returns:
            Dict con información de la organización
        """
        try:
            self.logger.info(f"Obteniendo información de organización - Key: {organization_key}")
            
            response = await self._make_request(
                endpoint="organizations/search",
                params={'organizations': organization_key}
            )
            
            # Extraer la organización específica de la respuesta
            organizations = response.get('organizations', [])
            if organizations:
                return organizations[0]
            else:
                raise HTTPStatusError(f"Organización no encontrada: {organization_key}", request=None, response=None)
            
            self.logger.info(f"Organización obtenida exitosamente - Key: {organization_key}")
            return response
            
        except HTTPStatusError as e:
            self.logger.error(f"Error al obtener organización - Key: {organization_key}, Error: {str(e)}")
            raise
    
    async def get_all_organization_projects(
        self,
        organization_key: str,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener todos los proyectos de una organización
        
        Args:
            organization_key: Clave de la organización
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            Lista de proyectos
        """
        try:
            self.logger.info(f"Obteniendo proyectos de organización - Key: {organization_key}, Page: {page}")
            
            response = await self._make_request(
                endpoint="projects/search",
                params={
                    'organization': organization_key,
                    'p': page,
                    'ps': page_size
                }
            )
            
            projects = response.get('components', [])
            total = response.get('paging', {}).get('total', 0)
            
            self.logger.info(f"Proyectos obtenidos exitosamente - Organization: {organization_key}, Total: {total}, Page: {page}")
            return projects
            
        except HTTPStatusError as e:
            self.logger.error(f"Error al obtener proyectos - Organization: {organization_key}, Error: {str(e)}")
            raise
    
    async def get_project_metrics(
        self,
        project_key: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Obtener métricas de un proyecto
        
        Args:
            project_key: Clave del proyecto
            metrics: Lista de métricas a obtener
            
        Returns:
            Dict con métricas del proyecto
        """
        try:
            if not metrics:
                metrics = [
                    'coverage', 'duplicated_lines_density', 'sqale_rating',
                    'reliability_rating', 'security_rating', 'security_review_rating',
                    'bugs', 'vulnerabilities', 'code_smells', 'new_issues',
                    'security_hotspots', 'security_hotspots_reviewed',
                    'lines', 'ncloc', 'alert_status', 'quality_gate_status'
                ]
            
            self.logger.info(f"Obteniendo métricas de proyecto - Key: {project_key}")
            
            response = await self._make_request(
                endpoint="measures/component",
                params={
                    'component': project_key,
                    'metricKeys': ','.join(metrics)
                }
            )
            
            # Convertir respuesta a formato más manejable
            metrics_data = {}
            component = response.get('component', {})
            
            for measure in component.get('measures', []):
                metric_key = measure.get('metric')
                value = measure.get('value')
                if metric_key and value is not None:
                    metrics_data[metric_key] = value
            
            self.logger.info(f"Métricas obtenidas exitosamente - Project: {project_key}, Metrics: {len(metrics_data)}")
            return metrics_data
            
        except HTTPStatusError as e:
            self.logger.error(f"Error al obtener métricas - Project: {project_key}, Error: {str(e)}")
            raise
    
    async def get_project_issues(
        self,
        project_key: str,
        page: int = 1,
        page_size: int = 100,
        statuses: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener issues de un proyecto
        
        Args:
            project_key: Clave del proyecto
            page: Número de página
            page_size: Tamaño de página
            statuses: Estados de issues a filtrar
            
        Returns:
            Lista de issues
        """
        try:
            if not statuses:
                statuses = ['OPEN', 'CONFIRMED', 'REOPENED', 'RESOLVED', 'CLOSED']
            
            self.logger.info(f"Obteniendo issues de proyecto - Key: {project_key}, Page: {page}")
            
            params = {
                'componentKeys': project_key,
                'p': page,
                'ps': page_size,
                'statuses': ','.join(statuses)
            }
            
            response = await self._make_request(
                endpoint="issues/search",
                params=params
            )
            
            issues = response.get('issues', [])
            total = response.get('total', 0)
            
            self.logger.info(f"Issues obtenidos exitosamente - Project: {project_key}, Total: {total}, Page: {page}")
            return issues
            
        except HTTPStatusError as e:
            self.logger.error(f"Error al obtener issues - Project: {project_key}, Error: {str(e)}")
            raise
    
    async def get_project_security_hotspots(
        self,
        project_key: str,
        page: int = 1,
        page_size: int = 100,
        statuses: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener security hotspots de un proyecto
        
        Args:
            project_key: Clave del proyecto
            page: Número de página
            page_size: Tamaño de página
            statuses: Estados de hotspots a filtrar
            
        Returns:
            Lista de security hotspots
        """
        try:
            if not statuses:
                statuses = ['TO_REVIEW', 'REVIEWED', 'SAFE', 'FIXED']
            
            self.logger.info(f"Obteniendo security hotspots de proyecto - Key: {project_key}, Page: {page}")
            
            params = {
                'projectKey': project_key,
                'p': page,
                'ps': page_size,
                'status': ','.join(statuses)
            }
            
            response = await self._make_request(
                endpoint="hotspots/search",
                params=params
            )
            
            hotspots = response.get('hotspots', [])
            total = response.get('paging', {}).get('total', 0)
            
            self.logger.info(f"Security hotspots obtenidos exitosamente - Project: {project_key}, Total: {total}, Page: {page}")
            return hotspots
            
        except HTTPStatusError as e:
            self.logger.error(f"Error al obtener security hotspots - Project: {project_key}, Error: {str(e)}")
            raise
    
    async def get_project_quality_gates(
        self,
        project_key: str
    ) -> Dict[str, Any]:
        """
        Obtener quality gate de un proyecto
        
        Args:
            project_key: Clave del proyecto
            
        Returns:
            Dict con información del quality gate
        """
        try:
            self.logger.info(f"Obteniendo quality gate de proyecto - Key: {project_key}")
            
            response = await self._make_request(
                endpoint="qualitygates/project_status",
                params={'projectKey': project_key}
            )
            
            self.logger.info(f"Quality gate obtenido exitosamente - Project: {project_key}")
            return response
            
        except HTTPStatusError as e:
            self.logger.error(f"Error al obtener quality gate - Project: {project_key}, Error: {str(e)}")
            raise
    
    async def get_project_details(self, project_key: str) -> Dict[str, Any]:
        """
        Obtener detalles completos de un proyecto
        
        Args:
            project_key: Clave del proyecto
            
        Returns:
            Dict con detalles del proyecto
        """
        try:
            self.logger.info(f"Obteniendo detalles de proyecto - Key: {project_key}")
            
            response = await self._make_request(
                endpoint="projects/show",
                params={'key': project_key}
            )
            
            self.logger.info(f"Detalles de proyecto obtenidos exitosamente - Key: {project_key}")
            return response.get('project', {})
            
        except HTTPStatusError as e:
            self.logger.error(f"Error al obtener detalles de proyecto - Key: {project_key}, Error: {str(e)}")
            raise
    
    async def get_all_projects_with_metrics(
        self,
        organization_key: str,
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtener todos los proyectos con sus métricas
        
        Args:
            organization_key: Clave de la organización
            batch_size: Tamaño del lote para procesamiento
            
        Returns:
            Lista de proyectos con métricas
        """
        try:
            self.logger.info(f"Obteniendo todos los proyectos con métricas - Organization: {organization_key}")
            
            all_projects = []
            page = 1
            page_size = 100
            
            while True:
                # Obtener proyectos de la página actual
                projects = await self.get_all_organization_projects(
                    organization_key, page, page_size
                )
                
                if not projects:
                    break
                
                # Procesar proyectos en lotes
                for i in range(0, len(projects), batch_size):
                    batch = projects[i:i + batch_size]
                    
                    # Obtener métricas para cada proyecto del lote
                    for project in batch:
                        try:
                            project_key = project.get('key')
                            if project_key:
                                metrics = await self.get_project_metrics(project_key)
                                project['metrics'] = metrics
                                
                                # Pausa entre proyectos para evitar rate limiting
                                await asyncio.sleep(0.1)
                                
                        except Exception as e:
                            self.logger.error(f"Error al obtener métricas para proyecto {project.get('key')}: {str(e)}")
                            project['metrics'] = {}
                    
                    # Pausa entre lotes
                    if len(batch) == batch_size:
                        await asyncio.sleep(1)
                
                all_projects.extend(projects)
                
                # Verificar si hay más páginas
                if len(projects) < page_size:
                    break
                
                page += 1
            
            self.logger.info(f"Proyectos con métricas obtenidos exitosamente - Organization: {organization_key}, Total: {len(all_projects)}")
            return all_projects
            
        except Exception as e:
            self.logger.error(f"Error al obtener proyectos con métricas - Organization: {organization_key}, Error: {str(e)}")
            raise
    
    def sort_projects_by_priority(
        self,
        projects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Ordenar proyectos por prioridad según criterios de calidad
        
        Args:
            projects: Lista de proyectos
            
        Returns:
            Lista de proyectos ordenados por prioridad
        """
        def get_priority_score(project: Dict[str, Any]) -> tuple:
            """Calcular score de prioridad para ordenamiento"""
            metrics = project.get('metrics', {})
            
            # Coverage (mayor es mejor)
            coverage = float(metrics.get('coverage', 0))
            
            # Duplications (menor es mejor)
            duplications = float(metrics.get('duplicated_lines_density', 0))
            
            # New issues (menor es mejor)
            new_issues = int(metrics.get('new_issues', 0))
            
            # Security hotspots (menor es mejor)
            security_hotspots = int(metrics.get('security_hotspots', 0))
            
            # Quality gate status (PASSED es mejor)
            quality_gate_status = metrics.get('quality_gate_status', 'FAILED')
            quality_gate_score = 1 if quality_gate_status == 'PASSED' else 0
            
            # Score de prioridad (mayor = más prioritario)
            priority_score = (
                coverage * 0.3 +  # 30% peso
                (100 - duplications) * 0.2 +  # 20% peso (invertido)
                max(0, 100 - new_issues * 10) * 0.2 +  # 20% peso (invertido)
                max(0, 100 - security_hotspots * 5) * 0.2 +  # 20% peso (invertido)
                quality_gate_score * 100 * 0.1  # 10% peso
            )
            
            return (-priority_score, -coverage, duplications, new_issues, security_hotspots)
        
        sorted_projects = sorted(projects, key=get_priority_score)
        
        self.logger.info(f"Proyectos ordenados por prioridad - Total: {len(sorted_projects)}")
        return sorted_projects
