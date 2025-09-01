"""
Servicio de lógica de negocio para repositorios

Implementa la lógica principal para:
- Obtener repositorios de Bitbucket
- Almacenar en base de datos
- Calcular métricas DevOps
- Generar reportes
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from src.api.bitbucket_client import BitbucketClient
from src.database.repositories import RepositoryRepository, CommitRepository, PullRequestRepository, WorkspaceRepository, ProjectRepository
from src.database.connection import get_db_session
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RepositoryService:
    """
    Servicio principal para gestión de repositorios
    
    Coordina la obtención de datos desde Bitbucket y su almacenamiento
    en la base de datos, incluyendo el cálculo de métricas DevOps
    """
    
    def __init__(self, bitbucket_client: BitbucketClient):
        """
        Inicializar servicio de repositorios
        
        Args:
            bitbucket_client: Cliente de la API de Bitbucket
        """
        self.bitbucket_client = bitbucket_client
        logger.info("Servicio de repositorios inicializado")
    
    async def get_workspace_repositories(
        self,
        workspace_slug: str,
        include_metrics: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Obtener todos los repositorios de un workspace
        
        Args:
            workspace_slug: Slug del workspace
            include_metrics: Si incluir métricas detalladas
            
        Returns:
            Lista de repositorios con información básica
        """
        logger.info(f"Obteniendo repositorios del workspace - Workspace: {workspace_slug}, Include metrics: {include_metrics}")
        
        try:
            # Obtener repositorios desde Bitbucket
            repositories = await self.bitbucket_client.get_all_workspace_repositories(workspace_slug)
            
            logger.info(f"Repositorios obtenidos desde Bitbucket - Workspace: {workspace_slug}, Total: {len(repositories)}")
            
            if include_metrics:
                # Enriquecer con métricas adicionales
                enriched_repos = []
                for repo in repositories:
                    enriched_repo = await self._enrich_repository_data(repo, workspace_slug)
                    enriched_repos.append(enriched_repo)
                return enriched_repos
            
            return repositories
            
        except Exception as e:
            logger.error(f"Error al obtener repositorios del workspace - Workspace: {workspace_slug}, Error: {str(e)}")
            raise
    
    async def get_project_repositories(
        self,
        workspace_slug: str,
        project_key: str,
        include_metrics: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Obtener todos los repositorios de un proyecto específico
        
        Args:
            workspace_slug: Slug del workspace
            project_key: Clave del proyecto
            include_metrics: Si incluir métricas detalladas
            
        Returns:
            Lista de repositorios del proyecto
        """
        logger.info(f"Obteniendo repositorios del proyecto - Workspace: {workspace_slug}, Project: {project_key}, Include metrics: {include_metrics}")
        
        try:
            # Obtener repositorios desde Bitbucket
            repositories = await self.bitbucket_client.get_all_project_repositories(
                workspace_slug, project_key
            )
            
            logger.info(f"Repositorios del proyecto obtenidos desde Bitbucket - Workspace: {workspace_slug}, Project: {project_key}, Total: {len(repositories)}")
            
            if include_metrics:
                # Enriquecer con métricas adicionales
                enriched_repos = []
                for repo in repositories:
                    enriched_repo = await self._enrich_repository_data(repo, workspace_slug, project_key)
                    enriched_repos.append(enriched_repo)
                return enriched_repos
            
            return repositories
            
        except Exception as e:
            logger.error(f"Error al obtener repositorios del proyecto - Workspace: {workspace_slug}, Project: {project_key}, Error: {str(e)}")
            raise
    
    async def get_repository(
        self,
        workspace_slug: str,
        repository_slug: str,
        include_metrics: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener información detallada de un repositorio específico
        
        Args:
            workspace_slug: Slug del workspace
            repository_slug: Slug del repositorio
            include_metrics: Si incluir métricas detalladas
            
        Returns:
            Información del repositorio o None si no existe
        """
        logger.info(f"Obteniendo información del repositorio - Workspace: {workspace_slug}, Repository: {repository_slug}, Include metrics: {include_metrics}")
        
        try:
            # Obtener repositorio desde Bitbucket
            repository = await self.bitbucket_client.get_repository(workspace_slug, repository_slug)
            
            if not repository:
                logger.warning(f"Repositorio no encontrado - Workspace: {workspace_slug}, Repository: {repository_slug}")
                return None
            
            logger.info(f"Repositorio obtenido desde Bitbucket - Workspace: {workspace_slug}, Repository: {repository_slug}, Name: {repository.get('name')}")
            
            if include_metrics:
                # Enriquecer con métricas adicionales
                enriched_repo = await self._enrich_repository_data(repository, workspace_slug)
                return enriched_repo
            
            return repository
            
        except Exception as e:
            logger.error(f"Error al obtener repositorio - Workspace: {workspace_slug}, Repository: {repository_slug}, Error: {str(e)}")
            raise
    
    async def sync_repository_to_database(
        self,
        workspace_slug: str,
        repository_slug: str,
        project_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sincronizar repositorio desde Bitbucket a la base de datos
        
        Args:
            workspace_slug: Slug del workspace
            repository_slug: Slug del repositorio
            project_key: Clave del proyecto (opcional)
            
        Returns:
            Repositorio sincronizado o None si falla
        """
        logger.info(f"Sincronizando repositorio a base de datos - Workspace: {workspace_slug}, Repository: {repository_slug}, Project: {project_key}")
        
        try:
            # Obtener información del repositorio desde Bitbucket
            repository_data = await self.bitbucket_client.get_repository(workspace_slug, repository_slug)
            
            if not repository_data:
                logger.warning(f"Repositorio no encontrado en Bitbucket - Workspace: {workspace_slug}, Repository: {repository_slug}")
                return None
            
            # Obtener IDs de workspace y proyecto
            workspace_id = await self._get_workspace_id(workspace_slug)
            project_id = None
            if project_key:
                project_id = await self._get_project_id(workspace_slug, project_key)
            
            # Guardar en base de datos
            with get_db_session() as session:
                repo_repo = RepositoryRepository(session)
                #commit_repo = CommitRepository(session)
                #pr_repo = PullRequestRepository(session)
                
                # Crear o actualizar repositorio
                repository = repo_repo.create_or_update(
                    repository_data, workspace_id, project_id
                )
                
                # Sincronizar commits
                # await self._sync_repository_commits(
                #     workspace_slug, repository_slug, repository.id, commit_repo
                # )
                
                # Sincronizar pull requests
                # await self._sync_repository_pull_requests(
                #     workspace_slug, repository_slug, repository.id, pr_repo
                # )
                
                # Obtener resumen completo
                repository_summary = repo_repo.get_repository_summary(repository.id)
                
                logger.info(f"Repositorio sincronizado exitosamente - Workspace: {workspace_slug}, Repository: {repository_slug}, ID: {repository.id}")
                
                return repository_summary
                
        except Exception as e:
            logger.error(f"Error al sincronizar repositorio - Workspace: {workspace_slug}, Repository: {repository_slug}, Error: {str(e)}")
            raise
    
    async def sync_workspace_repositories(
        self,
        workspace_slug: str,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Sincronizar todos los repositorios de un workspace
        
        Args:
            workspace_slug: Slug del workspace
            batch_size: Tamaño del lote para procesamiento
            
        Returns:
            Resumen de la sincronización
        """
        logger.info(f"Iniciando sincronización de repositorios del workspace - Workspace: {workspace_slug}, Batch size: {batch_size}")
        
        start_time = datetime.now()
        total_repositories = 0
        successful_syncs = 0
        failed_syncs = 0
        
        try:
            # Obtener todos los repositorios del workspace
            repositories = await self.bitbucket_client.get_all_workspace_repositories(workspace_slug)
            total_repositories = len(repositories)
            
            logger.info(f"Repositorios encontrados para sincronización - Workspace: {workspace_slug}, Total: {total_repositories}")
            
            # Procesar en lotes
            for i in range(0, total_repositories, batch_size):
                batch = repositories[i:i + batch_size]
                logger.info(f"Procesando lote de repositorios - Workspace: {workspace_slug}, Batch: {i // batch_size + 1}, Size: {len(batch)}")
                # Procesar cada repositorio del lote actual
                for repo in batch:
                    try:
                        await self.sync_repository_to_database(
                            workspace_slug, repo['slug']
                        )
                        successful_syncs += 1
                    except Exception as e:
                        failed_syncs += 1
                        logger.error(f"Error al sincronizar repositorio en lote - Workspace: {workspace_slug}, Repository: {repo['slug']}, Error: {str(e)}")
                
                # Pequeña pausa entre lotes para no sobrecargar la API
                await asyncio.sleep(1)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            sync_summary = {
                'workspace_slug': workspace_slug,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'total_repositories': total_repositories,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'success_rate': (successful_syncs / total_repositories * 100) if total_repositories > 0 else 0
            }
            
            logger.info(f"Sincronización de workspace completada - Workspace: {workspace_slug}, Summary: {sync_summary}")
            
            return sync_summary
            
        except Exception as e:
            logger.error(f"Error en sincronización de workspace - Workspace: {workspace_slug}, Error: {str(e)}")
            raise
    
    async def _enrich_repository_data(
        self,
        repository_data: Dict[str, Any],
        workspace_slug: str,
        project_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enriquecer datos del repositorio con métricas adicionales
        
        Args:
            repository_data: Datos básicos del repositorio
            workspace_slug: Slug del workspace
            project_key: Clave del proyecto (opcional)
            
        Returns:
            Repositorio enriquecido con métricas
        """
        try:
            # Agregar información de workspace y proyecto
            enriched_data = repository_data.copy()
            enriched_data['workspace_slug'] = workspace_slug
            if project_key:
                enriched_data['project_key'] = project_key
            

            
            # Agregar timestamp de enriquecimiento
            enriched_data['enriched_at'] = datetime.now().isoformat()
            
            return enriched_data
            
        except Exception as e:
            logger.error(
                "Error al enriquecer datos del repositorio",
                repository_slug=repository_data.get('slug'),
                error=str(e)
            )
            return repository_data
    
    async def _sync_repository_commits(
        self,
        workspace_slug: str,
        repository_slug: str,
        repository_id: int,
        commit_repo: CommitRepository
    ) -> None:
        """
        Sincronizar commits de un repositorio
        
        Args:
            workspace_slug: Slug del workspace
            repository_slug: Slug del repositorio
            repository_id: ID del repositorio en la base de datos
            commit_repo: Repositorio de commits
        """
        try:
            # Obtener commits desde Bitbucket (limitado a los últimos 100)
            commits = await self.bitbucket_client.get_repository_commits(
                workspace_slug, repository_slug, page=1, page_size=100
            )
            
            logger.debug(f"Commits obtenidos para sincronización - Workspace: {workspace_slug}, Repository: {repository_slug}, Total: {len(commits)}")
            
            # Guardar commits en base de datos
            for commit_data in commits:
                commit_repo.create_or_update(commit_data, repository_id)
            
            logger.debug(f"Commits sincronizados exitosamente - Workspace: {workspace_slug}, Repository: {repository_slug}, Total: {len(commits)}")
            
        except Exception as e:
            logger.error(f"Error al sincronizar commits - Workspace: {workspace_slug}, Repository: {repository_slug}, Error: {str(e)}")
            # No fallar la sincronización completa por errores en commits
    
    async def _sync_repository_pull_requests(
        self,
        workspace_slug: str,
        repository_slug: str,
        repository_id: int,
        pr_repo: PullRequestRepository
    ) -> None:
        """
        Sincronizar pull requests de un repositorio
        
        Args:
            workspace_slug: Slug del workspace
            repository_slug: Slug del repositorio
            repository_id: ID del repositorio en la base de datos
            pr_repo: Repositorio de pull requests
        """
        try:
            # Obtener pull requests desde Bitbucket (limitado a los últimos 100)
            pull_requests = await self.bitbucket_client.get_repository_pull_requests(
                workspace_slug, repository_slug, page=1, page_size=100
            )
            
            logger.debug(f"Pull requests obtenidos para sincronización - Workspace: {workspace_slug}, Repository: {repository_slug}, Total: {len(pull_requests)}")
            
            # Guardar pull requests en base de datos
            for pr_data in pull_requests:
                pr_repo.create_or_update(pr_data, repository_id)
            
            logger.debug(f"Pull requests sincronizados exitosamente - Workspace: {workspace_slug}, Repository: {repository_slug}, Total: {len(pull_requests)}")
            
        except Exception as e:
            logger.error(f"Error al sincronizar pull requests - Workspace: {workspace_slug}, Repository: {repository_slug}, Error: {str(e)}")
            # No fallar la sincronización completa por errores en pull requests
    
    async def _get_workspace_id(self, workspace_slug: str) -> int:
        """
        Obtener ID del workspace desde la base de datos
        
        Args:
            workspace_slug: Slug del workspace
            
        Returns:
            ID del workspace
            
        Raises:
            ValueError: Si el workspace no existe
        """
        try:
            # Obtener información del workspace desde Bitbucket
            workspace_data = await self.bitbucket_client.get_workspace(workspace_slug)
            
            if not workspace_data:
                raise ValueError(f"Workspace {workspace_slug} no encontrado en Bitbucket")
            
            # Crear o actualizar workspace en base de datos
            with get_db_session() as session:
                workspace_repo = WorkspaceRepository(session)
                workspace = workspace_repo.create_or_update(workspace_data)
                return workspace.id
                
        except Exception as e:
            logger.error(f"Error al obtener workspace ID - Workspace: {workspace_slug}, Error: {str(e)}")
            raise
    
    async def _get_project_id(self, workspace_slug: str, project_key: str) -> int:
        """
        Obtener ID del proyecto desde la base de datos
        
        Args:
            workspace_slug: Slug del workspace
            project_key: Clave del proyecto
            
        Returns:
            ID del proyecto
            
        Raises:
            ValueError: Si el proyecto no existe
        """
        try:
            # Obtener información del proyecto desde Bitbucket
            project_data = await self.bitbucket_client.get_project(workspace_slug, project_key)
            
            if not project_data:
                raise ValueError(f"Proyecto {project_key} no encontrado en Bitbucket")
            
            # Obtener workspace_id primero
            workspace_id = await self._get_workspace_id(workspace_slug)
            
            # Crear o actualizar proyecto en base de datos
            with get_db_session() as session:
                project_repo = ProjectRepository(session)
                project = project_repo.create_or_update(project_data, workspace_id)
                return project.id
                
        except Exception as e:
            logger.error(f"Error al obtener project ID - Workspace: {workspace_slug}, Project: {project_key}, Error: {str(e)}")
            raise

    async def sync_workspace_projects(
        self,
        workspace_slug: str,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Sincronizar todos los proyectos de un workspace
        
        Args:
            workspace_slug: Slug del workspace
            batch_size: Tamaño del lote para procesamiento
            
        Returns:
            Resumen de la sincronización
        """
        logger.info(f"Iniciando sincronización de proyectos del workspace - Workspace: {workspace_slug}, Batch size: {batch_size}")
        
        start_time = datetime.now()
        total_projects = 0
        successful_syncs = 0
        failed_syncs = 0
        
        try:
            # Obtener todos los proyectos del workspace
            projects = await self.bitbucket_client.get_all_workspace_projects(workspace_slug)
            total_projects = len(projects)
            
            logger.info(f"Proyectos encontrados para sincronización - Workspace: {workspace_slug}, Total: {total_projects}")
            
            # Procesar en lotes
            for i in range(0, total_projects, batch_size):
                batch = projects[i:i + batch_size]
                logger.info(f"Procesando lote de proyectos - Workspace: {workspace_slug}, Batch: {i // batch_size + 1}, Size: {len(batch)}")
                
                # Procesar cada proyecto del lote actual
                for project in batch:
                    try:
                        await self._sync_project_to_database(workspace_slug, project)
                        successful_syncs += 1
                        logger.debug(f"Proyecto sincronizado exitosamente - Workspace: {workspace_slug}, Project: {project.get('key')}")
                    except Exception as e:
                        failed_syncs += 1
                        logger.error(f"Error al sincronizar proyecto - Workspace: {workspace_slug}, Project: {project.get('key')}, Error: {str(e)}")
                
                # Pausa entre lotes para respetar rate limits
                if i + batch_size < total_projects:
                    logger.debug(f"Pausa entre lotes - Workspace: {workspace_slug}, Esperando 1 segundo")
                    await asyncio.sleep(1)
            
            # Calcular estadísticas
            duration = datetime.now() - start_time
            success_rate = (successful_syncs / total_projects * 100) if total_projects > 0 else 0
            
            sync_summary = {
                'total_projects': total_projects,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'success_rate': success_rate,
                'duration_seconds': duration.total_seconds(),
                'workspace_slug': workspace_slug
            }
            
            logger.info(f"Sincronización de proyectos completada - Workspace: {workspace_slug}, Success rate: {success_rate:.1f}%")
            return sync_summary
            
        except Exception as e:
            logger.error(f"Error en sincronización de proyectos - Workspace: {workspace_slug}, Error: {str(e)}")
            raise

    async def _sync_project_to_database(
        self,
        workspace_slug: str,
        project_data: Dict[str, Any]
    ) -> None:
        """
        Sincronizar un proyecto específico a la base de datos
        
        Args:
            workspace_slug: Slug del workspace
            project_data: Datos del proyecto desde Bitbucket
        """
        try:
            # Obtener workspace_id
            workspace_id = await self._get_workspace_id(workspace_slug)
            
            # Crear o actualizar proyecto en base de datos
            with get_db_session() as session:
                project_repo = ProjectRepository(session)
                project = project_repo.create_or_update(project_data, workspace_id)
                
                logger.debug(f"Proyecto sincronizado - Workspace: {workspace_slug}, Project: {project.key}, ID: {project.id}")
                
        except Exception as e:
            logger.error(f"Error al sincronizar proyecto - Workspace: {workspace_slug}, Project: {project_data.get('key')}, Error: {str(e)}")
            raise
