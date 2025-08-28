"""
Servicio de proyectos para SonarCloud

Proporciona lógica de negocio para el procesamiento y gestión
de proyectos de SonarCloud, incluyendo sincronización con la API
y almacenamiento en base de datos.
"""

import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..api.sonarcloud_client import SonarCloudClient
from ..database.repositories import ProjectRepository, OrganizationRepository
from ..models import Project, Organization
from ..utils.logger import get_logger
from ..config.settings import get_settings


class ProjectService:
    """
    Servicio para gestión de proyectos de SonarCloud
    
    Maneja la lógica de negocio para obtener, procesar y almacenar
    datos de proyectos desde SonarCloud API.
    """
    
    def __init__(self):
        """Inicializar servicio de proyectos"""
        self.client = SonarCloudClient()
        self.project_repo = ProjectRepository()
        self.org_repo = OrganizationRepository()
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        self.logger.info("Servicio de proyectos inicializado")
    
    async def sync_organization_projects(
        self,
        session: Session,
        organization_key: str,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Sincronizar todos los proyectos de una organización
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            batch_size: Tamaño del lote para procesamiento
            
        Returns:
            Dict con estadísticas de sincronización
        """
        try:
            if not batch_size:
                batch_size = self.settings.batch_size
            
            self.logger.info(f"Iniciando sincronización de proyectos - Organization: {organization_key}")
            
            # Obtener o crear organización
            organization = await self._get_or_create_organization(session, organization_key)
            if not organization:
                raise ValueError(f"No se pudo obtener/crear la organización: {organization_key}")
            
            # Obtener todos los proyectos con métricas desde SonarCloud
            projects_data = await self.client.get_all_projects_with_metrics(
                organization_key, batch_size
            )
            
            self.logger.info(f"Proyectos obtenidos desde SonarCloud - Total: {len(projects_data)}")
            
            # Procesar proyectos en lotes
            processed_count = 0
            created_count = 0
            updated_count = 0
            error_count = 0
            
            for i in range(0, len(projects_data), batch_size):
                batch = projects_data[i:i + batch_size]
                
                for project_data in batch:
                    try:
                        # Procesar proyecto individual
                        result = await self._process_project(
                            session, project_data, organization.id
                        )
                        
                        if result['action'] == 'created':
                            created_count += 1
                        elif result['action'] == 'updated':
                            updated_count += 1
                        
                        processed_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"Error al procesar proyecto {project_data.get('key')}: {str(e)}")
                        error_count += 1
                
                # Pausa entre lotes
                if i + batch_size < len(projects_data):
                    await asyncio.sleep(1)
            
            # Actualizar métricas de la organización
            await self._update_organization_metrics(session, organization.id)
            
            stats = {
                'organization_key': organization_key,
                'total_projects': len(projects_data),
                'processed_count': processed_count,
                'created_count': created_count,
                'updated_count': updated_count,
                'error_count': error_count
            }
            
            self.logger.info(f"Sincronización completada - Stats: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error en sincronización de proyectos: {str(e)}")
            raise
    
    async def sync_single_project(
        self,
        session: Session,
        project_key: str,
        organization_key: str
    ) -> Dict[str, Any]:
        """
        Sincronizar un proyecto específico
        
        Args:
            session: Sesión de base de datos
            project_key: Clave del proyecto
            organization_key: Clave de la organización
            
        Returns:
            Dict con resultado de la sincronización
        """
        try:
            self.logger.info(f"Sincronizando proyecto individual - Key: {project_key}")
            
            # Obtener o crear organización
            organization = await self._get_or_create_organization(session, organization_key)
            if not organization:
                raise ValueError(f"No se pudo obtener/crear la organización: {organization_key}")
            
            # Obtener datos del proyecto desde SonarCloud
            project_details = await self.client.get_project_details(project_key)
            project_metrics = await self.client.get_project_metrics(project_key)
            
            # Combinar datos
            project_data = {**project_details, 'metrics': project_metrics}
            
            # Procesar proyecto
            result = await self._process_project(session, project_data, organization.id)
            
            self.logger.info(f"Proyecto sincronizado - Key: {project_key}, Action: {result['action']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error al sincronizar proyecto {project_key}: {str(e)}")
            raise
    
    async def get_projects_by_priority(
        self,
        session: Session,
        organization_key: str,
        limit: Optional[int] = None
    ) -> List[Project]:
        """
        Obtener proyectos ordenados por prioridad
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            limit: Límite de resultados
            
        Returns:
            Lista de proyectos ordenados por prioridad
        """
        try:
            self.logger.info(f"Obteniendo proyectos por prioridad - Organization: {organization_key}")
            
            # Obtener organización
            organization = self.org_repo.get_by_key(session, organization_key)
            if not organization:
                raise ValueError(f"Organización no encontrada: {organization_key}")
            
            # Obtener proyectos de la organización
            projects = self.project_repo.get_by_organization(session, organization.id)
            
            # Ordenar por score de calidad
            sorted_projects = sorted(
                projects,
                key=lambda p: p.get_quality_score(),
                reverse=True
            )
            
            if limit:
                sorted_projects = sorted_projects[:limit]
            
            self.logger.info(f"Proyectos obtenidos por prioridad - Total: {len(sorted_projects)}")
            return sorted_projects
            
        except Exception as e:
            self.logger.error(f"Error al obtener proyectos por prioridad: {str(e)}")
            raise
    
    async def get_projects_summary(
        self,
        session: Session,
        organization_key: str
    ) -> Dict[str, Any]:
        """
        Obtener resumen de proyectos de una organización
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            
        Returns:
            Dict con resumen de proyectos
        """
        try:
            self.logger.info(f"Generando resumen de proyectos - Organization: {organization_key}")
            
            # Obtener organización
            organization = self.org_repo.get_by_key(session, organization_key)
            if not organization:
                raise ValueError(f"Organización no encontrada: {organization_key}")
            
            # Obtener proyectos
            projects = self.project_repo.get_by_organization(session, organization.id)
            
            # Calcular estadísticas
            total_projects = len(projects)
            passed_quality_gate = len([p for p in projects if p.quality_gate_status == 'PASSED'])
            failed_quality_gate = len([p for p in projects if p.quality_gate_status == 'FAILED'])
            
            # Calcular promedios
            avg_coverage = sum(p.coverage for p in projects) / total_projects if total_projects > 0 else 0
            avg_duplications = sum(p.duplications for p in projects) / total_projects if total_projects > 0 else 0
            
            # Contar issues por severidad
            total_bugs = sum(p.bugs_count for p in projects)
            total_vulnerabilities = sum(p.vulnerabilities_count for p in projects)
            total_code_smells = sum(p.code_smells_count for p in projects)
            total_security_hotspots = sum(p.security_hotspots_count for p in projects)
            
            # Proyectos con mejor y peor calidad
            if projects:
                best_project = max(projects, key=lambda p: p.get_quality_score())
                worst_project = min(projects, key=lambda p: p.get_quality_score())
            else:
                best_project = None
                worst_project = None
            
            summary = {
                'organization_key': organization_key,
                'total_projects': total_projects,
                'quality_gate_stats': {
                    'passed': passed_quality_gate,
                    'failed': failed_quality_gate,
                    'pass_rate': (passed_quality_gate / total_projects * 100) if total_projects > 0 else 0
                },
                'average_metrics': {
                    'coverage': round(avg_coverage, 2),
                    'duplications': round(avg_duplications, 2)
                },
                'total_issues': {
                    'bugs': total_bugs,
                    'vulnerabilities': total_vulnerabilities,
                    'code_smells': total_code_smells,
                    'security_hotspots': total_security_hotspots
                },
                'best_project': {
                    'key': best_project.key,
                    'name': best_project.name,
                    'quality_score': round(best_project.get_quality_score(), 2)
                } if best_project else None,
                'worst_project': {
                    'key': worst_project.key,
                    'name': worst_project.name,
                    'quality_score': round(worst_project.get_quality_score(), 2)
                } if worst_project else None
            }
            
            self.logger.info(f"Resumen generado - Organization: {organization_key}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error al generar resumen de proyectos: {str(e)}")
            raise
    
    async def _get_or_create_organization(
        self,
        session: Session,
        organization_key: str
    ) -> Optional[Organization]:
        """
        Obtener o crear organización
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            
        Returns:
            Organización encontrada o creada
        """
        try:
            # Buscar organización existente
            organization = self.org_repo.get_by_key(session, organization_key)
            
            if not organization:
                # Obtener datos de la organización desde SonarCloud
                org_data = await self.client.get_organization(organization_key)
                
                # Crear organización
                organization = Organization.from_sonarcloud_data(org_data)
                session.add(organization)
                session.flush()
                
                self.logger.info(f"Organización creada - Key: {organization_key}")
            else:
                self.logger.debug(f"Organización encontrada - Key: {organization_key}")
            
            return organization
            
        except Exception as e:
            self.logger.error(f"Error al obtener/crear organización {organization_key}: {str(e)}")
            raise
    
    async def _process_project(
        self,
        session: Session,
        project_data: Dict[str, Any],
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Procesar datos de un proyecto
        
        Args:
            session: Sesión de base de datos
            project_data: Datos del proyecto desde SonarCloud
            organization_id: ID de la organización
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            project_key = project_data.get('key')
            
            # Buscar proyecto existente
            existing_project = self.project_repo.get_by_key(session, project_key)
            
            if existing_project:
                # Actualizar proyecto existente
                existing_project.update_from_sonarcloud_data(project_data)
                
                # Actualizar métricas de calidad
                metrics_data = project_data.get('metrics', {})
                existing_project.update_quality_metrics(metrics_data)
                
                session.flush()
                
                self.logger.debug(f"Proyecto actualizado - Key: {project_key}")
                return {'action': 'updated', 'project': existing_project}
                
            else:
                # Crear nuevo proyecto
                new_project = Project.from_sonarcloud_data(project_data, organization_id)
                
                # Actualizar métricas de calidad
                metrics_data = project_data.get('metrics', {})
                new_project.update_quality_metrics(metrics_data)
                
                session.add(new_project)
                session.flush()
                
                self.logger.debug(f"Proyecto creado - Key: {project_key}")
                return {'action': 'created', 'project': new_project}
                
        except Exception as e:
            self.logger.error(f"Error al procesar proyecto {project_data.get('key')}: {str(e)}")
            raise
    
    async def _update_organization_metrics(
        self,
        session: Session,
        organization_id: int
    ) -> None:
        """
        Actualizar métricas de la organización
        
        Args:
            session: Sesión de base de datos
            organization_id: ID de la organización
        """
        try:
            # Obtener proyectos de la organización
            projects = self.project_repo.get_by_organization(session, organization_id)
            
            # Calcular métricas
            total_projects = len(projects)
            total_issues = sum(
                p.bugs_count + p.vulnerabilities_count + p.code_smells_count
                for p in projects
            )
            total_security_hotspots = sum(p.security_hotspots_count for p in projects)
            
            # Actualizar organización
            organization = self.org_repo.get_by_id(session, organization_id)
            if organization:
                organization.update_metrics(
                    total_projects=total_projects,
                    total_issues=total_issues,
                    total_security_hotspots=total_security_hotspots
                )
                session.flush()
                
                self.logger.debug(f"Métricas de organización actualizadas - ID: {organization_id}")
                
        except Exception as e:
            self.logger.error(f"Error al actualizar métricas de organización {organization_id}: {str(e)}")
            raise
