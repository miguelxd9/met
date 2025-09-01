"""
Servicio de lógica de negocio para SonarCloud

Implementa la lógica principal para:
- Obtener datos de SonarCloud
- Almacenar en base de datos
- Vincular con repositorios de Bitbucket
- Generar reportes de calidad
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

from src.api.sonarcloud_client import SonarCloudClient
from src.database.sonarcloud_repositories import (
    OrganizationRepository, SonarCloudProjectRepository, IssueRepository,
    SecurityHotspotRepository, QualityGateRepository, MetricRepository
)
from src.database.repositories import RepositoryRepository
from src.database.connection import get_db_session
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SonarCloudService:
    """
    Servicio principal para gestión de SonarCloud
    
    Coordina la obtención de datos desde SonarCloud y su almacenamiento
    en la base de datos, incluyendo la vinculación con Bitbucket
    """
    
    def __init__(self, sonarcloud_client: SonarCloudClient):
        """
        Inicializar servicio de SonarCloud
        
        Args:
            sonarcloud_client: Cliente de la API de SonarCloud
        """
        self.sonarcloud_client = sonarcloud_client
        logger.info("Servicio de SonarCloud inicializado")
    
    async def sync_organization(self, organization_key: str) -> Optional[Dict[str, Any]]:
        """
        Sincronizar organización con base de datos
        
        Args:
            organization_key: Clave de la organización
            
        Returns:
            Información de la organización sincronizada o None si falla
        """
        logger.info(f"Sincronizando organización: {organization_key}")
        
        try:
            # Obtener datos de la organización desde SonarCloud
            organization_data = await self.sonarcloud_client.get_organization(organization_key)
            
            if not organization_data:
                logger.error(f"No se pudo obtener datos de la organización: {organization_key}")
                return None
            
            # Sincronizar con base de datos
            with get_db_session() as session:
                organization_repo = OrganizationRepository(session)
                organization = organization_repo.create_or_update(organization_data)
                
                logger.info(f"Organización sincronizada exitosamente - ID: {organization.id}, Key: {organization.key}")
                
                return {
                    'id': organization.id,
                    'key': organization.key,
                    'name': organization.name,
                    'description': organization.description
                }
                
        except Exception as e:
            logger.error(f"Error al sincronizar organización - Organization: {organization_key}, Error: {str(e)}")
            return None
    
    async def sync_organization_projects(
        self,
        organization_key: str,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Sincronizar todos los proyectos de una organización
        
        Args:
            organization_key: Clave de la organización
            batch_size: Tamaño del lote para procesamiento
            
        Returns:
            Resumen de la sincronización
        """
        logger.info(f"Iniciando sincronización de proyectos de la organización - Organization: {organization_key}, Batch size: {batch_size}")
        
        start_time = datetime.now()
        successful_syncs = 0
        failed_syncs = 0
        total_projects = 0
        
        try:
            # Primero sincronizar la organización
            organization = await self.sync_organization(organization_key)
            if not organization:
                raise Exception(f"No se pudo sincronizar la organización: {organization_key}")
            
            # Obtener todos los proyectos de la organización
            projects = await self.sonarcloud_client.get_all_organization_projects(organization_key)
            total_projects = len(projects)
            
            logger.info(f"Proyectos encontrados para sincronización - Organization: {organization_key}, Total: {total_projects}")
            
            # Procesar proyectos en lotes
            for i in range(0, total_projects, batch_size):
                batch = projects[i:i + batch_size]
                logger.info(f"Procesando lote de proyectos - Organization: {organization_key}, Batch: {i // batch_size + 1}, Size: {len(batch)}")
                
                for project_data in batch:
                    try:
                        # Sincronizar proyecto individual
                        project_result = await self._sync_project(project_data, organization['id'])
                        
                        if project_result:
                            successful_syncs += 1
                            logger.debug(f"Proyecto sincronizado exitosamente - Key: {project_data.get('key')}")
                        else:
                            failed_syncs += 1
                            logger.warning(f"Fallo al sincronizar proyecto - Key: {project_data.get('key')}")
                            
                    except Exception as e:
                        failed_syncs += 1
                        logger.error(f"Error al sincronizar proyecto - Key: {project_data.get('key')}, Error: {str(e)}")
                
                # Pausa entre lotes para no sobrecargar la API
                if i + batch_size < total_projects:
                    await asyncio.sleep(1)
            
            # Calcular estadísticas
            duration = datetime.now() - start_time
            success_rate = (successful_syncs / total_projects * 100) if total_projects > 0 else 0
            
            summary = {
                'total_projects': total_projects,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'success_rate': success_rate,
                'duration_seconds': duration.total_seconds()
            }
            
            logger.info(f"Sincronización de proyectos completada - Organization: {organization_key}, Summary: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Error en sincronización de proyectos - Organization: {organization_key}, Error: {str(e)}")
            raise
    
    async def _sync_project(self, project_data: Dict[str, Any], organization_id: int) -> Optional[Dict[str, Any]]:
        """
        Sincronizar un proyecto individual
        
        Args:
            project_data: Datos del proyecto desde SonarCloud
            organization_id: ID de la organización
            
        Returns:
            Información del proyecto sincronizado o None si falla
        """
        try:
            project_key = project_data.get('key')
            
            with get_db_session() as session:
                # Sincronizar proyecto
                project_repo = SonarCloudProjectRepository(session)
                project = project_repo.create_or_update(project_data, organization_id)
                
                # Intentar vincular con repositorio de Bitbucket
                if project.scm_url:
                    self._link_to_bitbucket_repository(project, session)
                
                # Sincronizar métricas del proyecto
                await self._sync_project_metrics(project_key, project.id, session)
                
                # Sincronizar quality gate
                await self._sync_project_quality_gate(project_key, project.id, session)
                
                logger.debug(f"Proyecto sincronizado exitosamente - Key: {project_key}, ID: {project.id}")
                
                return {
                    'id': project.id,
                    'key': project.key,
                    'name': project.name,
                    'scm_url': project.scm_url
                }
                
        except Exception as e:
            logger.error(f"Error al sincronizar proyecto - Key: {project_data.get('key')}, Error: {str(e)}")
            return None
    
    def _link_to_bitbucket_repository(self, sonarcloud_project: Any, session: Any) -> None:
        """
        Vincular proyecto de SonarCloud con repositorio de Bitbucket
        
        Args:
            sonarcloud_project: Proyecto de SonarCloud
            session: Sesión de base de datos
        """
        try:
            scm_url = sonarcloud_project.scm_url
            if not scm_url:
                return
            
            # Extraer nombre del repositorio de la URL SCM
            # Ejemplo: https://bitbucket.org/ibkteam/mmp-plin -> mmp-plin
            match = re.search(r'bitbucket\.org/[^/]+/([^/]+)', scm_url)
            if not match:
                return
            
            repository_name = match.group(1)
            
            # Buscar repositorio en Bitbucket por nombre
            repository_repo = RepositoryRepository(session)
            repository = repository_repo.get_by_slug(repository_name)
            
            if repository:
                # Vincular proyecto de SonarCloud con repositorio de Bitbucket
                sonarcloud_project.bitbucket_repository_id = repository.id
                session.commit()
                
                logger.info(f"Proyecto SonarCloud vinculado con repositorio Bitbucket - Project: {sonarcloud_project.key}, Repository: {repository_name}")
            else:
                logger.debug(f"No se encontró repositorio Bitbucket para vincular - Project: {sonarcloud_project.key}, Repository: {repository_name}")
                
        except Exception as e:
            logger.error(f"Error al vincular con repositorio Bitbucket - Project: {sonarcloud_project.key}, Error: {str(e)}")
    
    async def _sync_project_metrics(
        self,
        project_key: str,
        sonarcloud_project_id: int,
        session: Any
    ) -> None:
        """
        Sincronizar métricas de un proyecto
        
        Args:
            project_key: Clave del proyecto
            sonarcloud_project_id: ID del proyecto en la base de datos
            session: Sesión de base de datos
        """
        try:
            # Obtener métricas del proyecto
            metrics_data = await self.sonarcloud_client.get_project_metrics(project_key)
            
            if metrics_data:
                # Sincronizar métricas con base de datos
                metric_repo = MetricRepository(session)
                for metric_data in metrics_data:
                    metric_repo.create_or_update(metric_data, sonarcloud_project_id)
                
                logger.debug(f"Métricas sincronizadas - Project: {project_key}, Count: {len(metrics_data)}")
                
        except Exception as e:
            logger.error(f"Error al sincronizar métricas - Project: {project_key}, Error: {str(e)}")
    
    async def _sync_project_quality_gate(
        self,
        project_key: str,
        sonarcloud_project_id: int,
        session: Any
    ) -> None:
        """
        Sincronizar quality gate de un proyecto
        
        Args:
            project_key: Clave del proyecto
            sonarcloud_project_id: ID del proyecto en la base de datos
            session: Sesión de base de datos
        """
        try:
            # Obtener quality gate del proyecto
            quality_gate_data = await self.sonarcloud_client.get_project_quality_gate(project_key)
            
            if quality_gate_data:
                # Sincronizar quality gate con base de datos
                quality_gate_repo = QualityGateRepository(session)
                quality_gate_repo.create_or_update(quality_gate_data, sonarcloud_project_id)
                
                logger.debug(f"Quality gate sincronizado - Project: {project_key}")
                
        except Exception as e:
            logger.error(f"Error al sincronizar quality gate - Project: {project_key}, Error: {str(e)}")
    
    async def sync_project_details(
        self,
        project_key: str,
        include_issues: bool = True,
        include_security_hotspots: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Sincronizar detalles completos de un proyecto
        
        Args:
            project_key: Clave del proyecto
            include_issues: Si incluir issues
            include_security_hotspots: Si incluir security hotspots
            
        Returns:
            Información del proyecto sincronizado o None si falla
        """
        logger.info(f"Sincronizando detalles del proyecto: {project_key}")
        
        try:
            with get_db_session() as session:
                # Obtener proyecto de la base de datos
                project_repo = SonarCloudProjectRepository(session)
                project = project_repo.get_by_key(project_key)
                
                if not project:
                    logger.error(f"Proyecto no encontrado en la base de datos: {project_key}")
                    return None
                
                # Sincronizar issues si se solicita
                if include_issues:
                    await self._sync_project_issues(project_key, project.id, session)
                
                # Sincronizar security hotspots si se solicita
                if include_security_hotspots:
                    await self._sync_project_security_hotspots(project_key, project.id, session)
                
                logger.info(f"Detalles del proyecto sincronizados exitosamente - Key: {project_key}")
                
                return {
                    'id': project.id,
                    'key': project.key,
                    'name': project.name,
                    'scm_url': project.scm_url
                }
                
        except Exception as e:
            logger.error(f"Error al sincronizar detalles del proyecto - Key: {project_key}, Error: {str(e)}")
            return None
    
    async def _sync_project_issues(
        self,
        project_key: str,
        sonarcloud_project_id: int,
        session: Any
    ) -> None:
        """
        Sincronizar issues de un proyecto
        
        Args:
            project_key: Clave del proyecto
            sonarcloud_project_id: ID del proyecto en la base de datos
            session: Sesión de base de datos
        """
        try:
            # Obtener issues del proyecto
            issues_data = await self.sonarcloud_client.get_project_issues(project_key)
            
            if issues_data:
                # Sincronizar issues con base de datos
                issue_repo = IssueRepository(session)
                for issue_data in issues_data:
                    issue_repo.create_or_update(issue_data, sonarcloud_project_id)
                
                logger.debug(f"Issues sincronizados - Project: {project_key}, Count: {len(issues_data)}")
                
        except Exception as e:
            logger.error(f"Error al sincronizar issues - Project: {project_key}, Error: {str(e)}")
    
    async def _sync_project_security_hotspots(
        self,
        project_key: str,
        sonarcloud_project_id: int,
        session: Any
    ) -> None:
        """
        Sincronizar security hotspots de un proyecto
        
        Args:
            project_key: Clave del proyecto
            sonarcloud_project_id: ID del proyecto en la base de datos
            session: Sesión de base de datos
        """
        try:
            # Obtener security hotspots del proyecto
            hotspots_data = await self.sonarcloud_client.get_project_security_hotspots(project_key)
            
            if hotspots_data:
                # Sincronizar security hotspots con base de datos
                hotspot_repo = SecurityHotspotRepository(session)
                for hotspot_data in hotspots_data:
                    hotspot_repo.create_or_update(hotspot_data, sonarcloud_project_id)
                
                logger.debug(f"Security hotspots sincronizados - Project: {project_key}, Count: {len(hotspots_data)}")
                
        except Exception as e:
            logger.error(f"Error al sincronizar security hotspots - Project: {project_key}, Error: {str(e)}")
    
    async def get_project_summary(self, project_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtener resumen de un proyecto
        
        Args:
            project_key: Clave del proyecto
            
        Returns:
            Resumen del proyecto o None si no se encuentra
        """
        try:
            with get_db_session() as session:
                project_repo = SonarCloudProjectRepository(session)
                project = project_repo.get_by_key(project_key)
                
                if not project:
                    return None
                
                # Obtener métricas básicas
                metric_repo = MetricRepository(session)
                metrics = metric_repo.get_by_project(project.id)
                
                # Obtener quality gate
                quality_gate_repo = QualityGateRepository(session)
                quality_gate = quality_gate_repo.get_by_project(project.id)
                
                return {
                    'id': project.id,
                    'key': project.key,
                    'name': project.name,
                    'visibility': project.visibility,
                    'last_analysis_date': project.last_analysis_date.isoformat() if project.last_analysis_date else None,
                    'scm_url': project.scm_url,
                    'bitbucket_repository_id': project.bitbucket_repository_id,
                    'metrics_count': len(metrics),
                    'quality_gate_status': quality_gate.status.value if quality_gate else None
                }
                
        except Exception as e:
            logger.error(f"Error al obtener resumen del proyecto - Key: {project_key}, Error: {str(e)}")
            return None
