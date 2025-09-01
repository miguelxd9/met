"""
Repositorios de base de datos para el sistema de métricas DevOps

Implementa el patrón Repository para acceder a los datos de:
- Workspaces
- Projects
- Repositories
- Commits
- Pull Requests
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func

from src.models import (
    Workspace, Project, Repository, Commit, PullRequest
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseRepository:
    """Repositorio base con operaciones comunes"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, entity: Any) -> Any:
        """Agregar entidad a la sesión"""
        self.session.add(entity)
        return entity
    
    def commit(self):
        """Confirmar cambios"""
        self.session.commit()
    
    def rollback(self):
        """Revertir cambios"""
        self.session.rollback()
    
    def refresh(self, entity: Any):
        """Refrescar entidad desde la base de datos"""
        self.session.refresh(entity)


class WorkspaceRepository(BaseRepository):
    """Repositorio para entidades Workspace"""
    
    def get_by_id(self, workspace_id: int) -> Optional[Workspace]:
        """Obtener workspace por ID"""
        return self.session.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    def get_by_uuid(self, uuid: str) -> Optional[Workspace]:
        """Obtener workspace por UUID"""
        return self.session.query(Workspace).filter(Workspace.uuid == uuid).first()
    
    def get_by_slug(self, slug: str) -> Optional[Workspace]:
        """Obtener workspace por slug"""
        return self.session.query(Workspace).filter(Workspace.slug == slug).first()
    
    def get_by_bitbucket_id(self, bitbucket_id: str) -> Optional[Workspace]:
        """Obtener workspace por ID de Bitbucket"""
        return self.session.query(Workspace).filter(Workspace.bitbucket_id == bitbucket_id).first()
    
    def get_all(self) -> List[Workspace]:
        """Obtener todos los workspaces"""
        return self.session.query(Workspace).all()
    
    def get_all_with_metrics(self) -> List[Workspace]:
        """Obtener todos los workspaces con métricas cargadas"""
        return self.session.query(Workspace).options(
            joinedload(Workspace.projects),
            joinedload(Workspace.repositories)
        ).all()
    
    def create_or_update(self, workspace_data: Dict[str, Any]) -> Workspace:
        """
        Crear o actualizar workspace
        
        Args:
            workspace_data: Datos del workspace desde Bitbucket
            
        Returns:
            Workspace creado o actualizado
        """
        # Buscar por UUID primero
        existing = self.get_by_uuid(workspace_data.get('uuid'))
        
        # Si no se encuentra por UUID, buscar por slug
        if not existing:
            existing = self.get_by_slug(workspace_data.get('slug'))
        
        if existing:
            # Actualizar existente
            existing.update_from_bitbucket_data(workspace_data)
            logger.debug(f"Workspace actualizado - ID: {existing.id}, Slug: {existing.slug}")
            return existing
        else:
            # Crear nuevo
            new_workspace = Workspace.from_bitbucket_data(workspace_data)
            self.add(new_workspace)
            self.commit()
            logger.info(f"Nuevo workspace creado - ID: {new_workspace.id}, Slug: {new_workspace.slug}, Name: {new_workspace.name}")
            return new_workspace
    



class ProjectRepository(BaseRepository):
    """Repositorio para entidades Project"""
    
    def get_by_id(self, project_id: int) -> Optional[Project]:
        """Obtener proyecto por ID"""
        return self.session.query(Project).filter(Project.id == project_id).first()
    
    def get_by_uuid(self, uuid: str) -> Optional[Project]:
        """Obtener proyecto por UUID"""
        return self.session.query(Project).filter(Project.uuid == uuid).first()
    
    def get_by_key(self, key: str) -> Optional[Project]:
        """Obtener proyecto por clave"""
        return self.session.query(Project).filter(Project.key == key).first()
    
    def get_by_bitbucket_id(self, bitbucket_id: str) -> Optional[Project]:
        """Obtener proyecto por ID de Bitbucket"""
        return self.session.query(Project).filter(Project.bitbucket_id == bitbucket_id).first()
    
    def get_by_workspace(self, workspace_id: int) -> List[Project]:
        """Obtener proyectos por workspace"""
        return self.session.query(Project).filter(Project.workspace_id == workspace_id).all()
    
    def get_all(self) -> List[Project]:
        """Obtener todos los proyectos"""
        return self.session.query(Project).all()
    
    def get_all_with_metrics(self) -> List[Project]:
        """Obtener todos los proyectos con métricas cargadas"""
        return self.session.query(Project).options(
            joinedload(Project.workspace),
            joinedload(Project.repositories)
        ).all()
    
    def create_or_update(
        self,
        project_data: Dict[str, Any],
        workspace_id: int
    ) -> Project:
        """
        Crear o actualizar proyecto
        
        Args:
            project_data: Datos del proyecto desde Bitbucket
            workspace_id: ID del workspace al que pertenece
            
        Returns:
            Project creado o actualizado
        """
        # Buscar por UUID primero
        existing = self.get_by_uuid(project_data.get('uuid'))
        
        # Si no se encuentra por UUID, buscar por key
        if not existing:
            existing = self.get_by_key(project_data.get('key'))
        
        if existing:
            # Actualizar existente
            existing.update_from_bitbucket_data(project_data)
            logger.debug(f"Proyecto actualizado - ID: {existing.id}, Key: {existing.key}")
            return existing
        else:
            # Crear nuevo
            new_project = Project.from_bitbucket_data(project_data, workspace_id)
            self.add(new_project)
            self.commit()
            logger.info(f"Nuevo proyecto creado - ID: {new_project.id}, Key: {new_project.key}, Name: {new_project.name}, Workspace ID: {workspace_id}")
            return new_project
    



class RepositoryRepository(BaseRepository):
    """Repositorio para entidades Repository"""
    
    def get_by_id(self, repository_id: int) -> Optional[Repository]:
        """Obtener repositorio por ID"""
        return self.session.query(Repository).filter(Repository.id == repository_id).first()
    
    def get_by_uuid(self, uuid: str) -> Optional[Repository]:
        """Obtener repositorio por UUID"""
        return self.session.query(Repository).filter(Repository.uuid == uuid).first()
    
    def get_by_slug(self, slug: str) -> Optional[Repository]:
        """Obtener repositorio por slug"""
        return self.session.query(Repository).filter(Repository.slug == slug).first()
    
    def get_by_bitbucket_id(self, bitbucket_id: str) -> Optional[Repository]:
        """Obtener repositorio por ID de Bitbucket"""
        return self.session.query(Repository).filter(Repository.bitbucket_id == bitbucket_id).first()
    
    def get_by_workspace(self, workspace_id: int) -> List[Repository]:
        """Obtener repositorios por workspace"""
        return self.session.query(Repository).filter(Repository.workspace_id == workspace_id).all()
    
    def get_by_project(self, project_id: int) -> List[Repository]:
        """Obtener repositorios por proyecto"""
        return self.session.query(Repository).filter(Repository.project_id == project_id).all()
    
    def get_by_language(self, language: str) -> List[Repository]:
        """Obtener repositorios por lenguaje de programación"""
        return self.session.query(Repository).filter(Repository.language == language).all()
    
    def get_all(self) -> List[Repository]:
        """Obtener todos los repositorios"""
        return self.session.query(Repository).all()
    
    def get_all_with_metrics(self) -> List[Repository]:
        """Obtener todos los repositorios con métricas cargadas"""
        return self.session.query(Repository).options(
            joinedload(Repository.workspace),
            joinedload(Repository.project),
            joinedload(Repository.commits),
            joinedload(Repository.pull_requests)
        ).all()
    

    
    def create_or_update(
        self,
        repository_data: Dict[str, Any],
        workspace_id: int,
        project_id: Optional[int] = None
    ) -> Repository:
        """
        Crear o actualizar repositorio
        
        Args:
            repository_data: Datos del repositorio desde Bitbucket
            workspace_id: ID del workspace al que pertenece
            project_id: ID del proyecto al que pertenece (opcional)
            
        Returns:
            Repository creado o actualizado
        """
        # Buscar por UUID primero
        existing = self.get_by_uuid(repository_data.get('uuid'))
        
        # Si no se encuentra por UUID, buscar por slug
        if not existing:
            existing = self.get_by_slug(repository_data.get('slug'))
        
        if existing:
            # Actualizar existente
            existing.update_from_bitbucket_data(repository_data)
            
            # Actualizar project_id si se proporciona uno nuevo
            if project_id is not None:
                existing.project_id = project_id
                logger.debug(f"Project ID actualizado para repositorio - ID: {existing.id}, Slug: {existing.slug}, Project ID: {project_id}")
            
            logger.debug(f"Repositorio actualizado - ID: {existing.id}, Slug: {existing.slug}")
            return existing
        else:
            # Crear nuevo
            new_repository = Repository.from_bitbucket_data(
                repository_data, workspace_id, project_id
            )
            self.add(new_repository)
            self.commit()
            logger.info(f"Nuevo repositorio creado - ID: {new_repository.id}, Slug: {new_repository.slug}, Name: {new_repository.name}, Workspace ID: {workspace_id}, Project ID: {project_id}")
            return new_repository
    
    def update_devops_compliance(
        self,
        repository_id: int,
        compliance_data: Dict[str, bool]
    ) -> None:
        """Actualizar métricas de cumplimiento DevOps"""
        repository = self.get_by_id(repository_id)
        if repository:
            repository.update_devops_compliance(**compliance_data)
            self.commit()
            logger.debug(f"Cumplimiento DevOps del repositorio actualizado - Repository ID: {repository_id}, Compliance data: {compliance_data}")
    
    def get_repository_summary(self, repository_id: int) -> Optional[Dict[str, Any]]:
        """Obtener resumen completo del repositorio"""
        repository = self.get_by_id(repository_id)
        if not repository:
            return None
        
        return {
            'id': repository.id,
            'name': repository.name,
            'slug': repository.slug,
            'language': repository.language,
            'is_private': repository.is_private,
            'size_bytes': repository.size_bytes,
            'workspace': repository.workspace.name if repository.workspace else None,
            'project': repository.project.name if repository.project else None
        }


class CommitRepository(BaseRepository):
    """Repositorio para entidades Commit"""
    
    def get_by_id(self, commit_id: int) -> Optional[Commit]:
        """Obtener commit por ID"""
        return self.session.query(Commit).filter(Commit.id == commit_id).first()
    
    def get_by_hash(self, commit_hash: str) -> Optional[Commit]:
        """Obtener commit por hash"""
        return self.session.query(Commit).filter(Commit.hash == commit_hash).first()
    
    def get_by_bitbucket_id(self, bitbucket_id: str) -> Optional[Commit]:
        """Obtener commit por ID de Bitbucket"""
        return self.session.query(Commit).filter(Commit.bitbucket_id == bitbucket_id).first()
    
    def get_by_repository(self, repository_id: int) -> List[Commit]:
        """Obtener commits por repositorio"""
        return self.session.query(Commit).filter(Commit.repository_id == repository_id).all()
    
    def get_by_author(self, author_name: str) -> List[Commit]:
        """Obtener commits por autor"""
        return self.session.query(Commit).filter(Commit.author_name == author_name).all()
    
    def get_recent_commits(self, repository_id: int, limit: int = 10) -> List[Commit]:
        """Obtener commits recientes de un repositorio"""
        return self.session.query(Commit).filter(
            Commit.repository_id == repository_id
        ).order_by(desc(Commit.commit_date)).limit(limit).all()
    
    def get_commits_by_date_range(
        self,
        repository_id: int,
        start_date: str,
        end_date: str
    ) -> List[Commit]:
        """Obtener commits por rango de fechas"""
        return self.session.query(Commit).filter(
            and_(
                Commit.repository_id == repository_id,
                Commit.commit_date >= start_date,
                Commit.commit_date <= end_date
            )
        ).order_by(desc(Commit.commit_date)).all()
    
    def create_or_update(
        self,
        commit_data: Dict[str, Any],
        repository_id: int
    ) -> Commit:
        """
        Crear o actualizar commit
        
        Args:
            commit_data: Datos del commit desde Bitbucket
            repository_id: ID del repositorio al que pertenece
            
        Returns:
            Commit creado o actualizado
        """
        # Buscar por hash primero
        existing = self.get_by_hash(commit_data.get('hash'))
        
        if existing:
            # Actualizar existente
            existing.update_from_bitbucket_data(commit_data)
            logger.debug(f"Commit actualizado - ID: {existing.id}, Hash: {existing.hash[:8]}")
            return existing
        else:
            # Crear nuevo
            new_commit = Commit.from_bitbucket_data(commit_data, repository_id)
            self.add(new_commit)
            self.commit()
            logger.debug(f"Nuevo commit creado - ID: {new_commit.id}, Hash: {new_commit.hash[:8]}, Repository ID: {repository_id}")
            return new_commit
    
    def get_commit_statistics(self, repository_id: int) -> Dict[str, Any]:
        """Obtener estadísticas básicas de commits de un repositorio"""
        # Solo retornar información básica, sin cálculos
        return {
            'repository_id': repository_id,
            'has_commits': self.session.query(Commit).filter(
                Commit.repository_id == repository_id
            ).first() is not None
        }


class PullRequestRepository(BaseRepository):
    """Repositorio para entidades PullRequest"""
    
    def get_by_id(self, pr_id: int) -> Optional[PullRequest]:
        """Obtener pull request por ID"""
        return self.session.query(PullRequest).filter(PullRequest.id == pr_id).first()
    
    def get_by_bitbucket_id(self, bitbucket_id: str) -> Optional[PullRequest]:
        """Obtener pull request por ID de Bitbucket"""
        return self.session.query(PullRequest).filter(PullRequest.bitbucket_id == bitbucket_id).first()
    
    def get_by_repository(self, repository_id: int) -> List[PullRequest]:
        """Obtener pull requests por repositorio"""
        return self.session.query(PullRequest).filter(PullRequest.repository_id == repository_id).all()
    
    def get_by_state(self, state: str) -> List[PullRequest]:
        """Obtener pull requests por estado"""
        return self.session.query(PullRequest).filter(PullRequest.state == state).all()
    
    def get_open_pull_requests(self, repository_id: int) -> List[PullRequest]:
        """Obtener pull requests abiertos de un repositorio"""
        return self.session.query(PullRequest).filter(
            and_(
                PullRequest.repository_id == repository_id,
                PullRequest.state == 'OPEN'
            )
        ).all()
    
    def get_recent_pull_requests(self, repository_id: int, limit: int = 10) -> List[PullRequest]:
        """Obtener pull requests recientes de un repositorio"""
        return self.session.query(PullRequest).filter(
            PullRequest.repository_id == repository_id
        ).order_by(desc(PullRequest.created_date)).limit(limit).all()
    
    def get_pull_requests_by_date_range(
        self,
        repository_id: int,
        start_date: str,
        end_date: str
    ) -> List[PullRequest]:
        """Obtener pull requests por rango de fechas"""
        return self.session.query(PullRequest).filter(
            and_(
                PullRequest.repository_id == repository_id,
                PullRequest.created_date >= start_date,
                PullRequest.created_date <= end_date
            )
        ).order_by(desc(PullRequest.created_date)).all()
    
    def create_or_update(
        self,
        pr_data: Dict[str, Any],
        repository_id: int
    ) -> PullRequest:
        """
        Crear o actualizar pull request
        
        Args:
            pr_data: Datos del pull request desde Bitbucket
            repository_id: ID del repositorio al que pertenece
            
        Returns:
            PullRequest creado o actualizado
        """
        # Buscar por ID de Bitbucket primero
        existing = self.get_by_bitbucket_id(pr_data.get('id'))
        
        if existing:
            # Actualizar existente
            existing.update_from_bitbucket_data(pr_data)
            logger.debug(f"Pull request actualizado - ID: {existing.id}, Bitbucket ID: {existing.bitbucket_id}")
            return existing
        else:
            # Crear nuevo
            new_pr = PullRequest.from_bitbucket_data(pr_data, repository_id)
            self.add(new_pr)
            self.commit()
            logger.info(f"Nuevo pull request creado - ID: {new_pr.id}, Bitbucket ID: {new_pr.bitbucket_id}, Title: {new_pr.title}, Repository ID: {repository_id}")
            return new_pr
    
    def get_pull_request_statistics(self, repository_id: int) -> Dict[str, Any]:
        """Obtener estadísticas de pull requests de un repositorio"""
        # Contar por estado
        open_count = self.session.query(PullRequest).filter(
            and_(
                PullRequest.repository_id == repository_id,
                PullRequest.state == 'OPEN'
            )
        ).count()
        
        merged_count = self.session.query(PullRequest).filter(
            and_(
                PullRequest.repository_id == repository_id,
                PullRequest.state == 'MERGED'
            )
        ).count()
        
        declined_count = self.session.query(PullRequest).filter(
            and_(
                PullRequest.repository_id == repository_id,
                PullRequest.state == 'DECLINED'
            )
        ).count()
        
        total_prs = open_count + merged_count + declined_count
        
        return {
            'total_prs': total_prs,
            'open_prs': open_count,
            'merged_prs': merged_count,
            'declined_prs': declined_count
        }
