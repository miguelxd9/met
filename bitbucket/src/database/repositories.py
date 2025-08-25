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
        
        if existing:
            # Actualizar existente
            existing.update_from_bitbucket_data(workspace_data)
            logger.debug(
                "Workspace actualizado",
                workspace_id=existing.id,
                slug=existing.slug
            )
            return existing
        else:
            # Crear nuevo
            new_workspace = Workspace.from_bitbucket_data(workspace_data)
            self.add(new_workspace)
            self.commit()
            logger.info(
                "Nuevo workspace creado",
                workspace_id=new_workspace.id,
                slug=new_workspace.slug,
                name=new_workspace.name
            )
            return new_workspace
    
    def update_metrics(
        self,
        workspace_id: int,
        total_repos: int,
        total_projects: int,
        total_members: int
    ) -> None:
        """Actualizar métricas del workspace"""
        workspace = self.get_by_id(workspace_id)
        if workspace:
            workspace.update_metrics(total_repos, total_projects, total_members)
            self.commit()
            logger.debug(
                "Métricas del workspace actualizadas",
                workspace_id=workspace_id,
                total_repos=total_repos,
                total_projects=total_projects,
                total_members=total_members
            )


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
        
        if existing:
            # Actualizar existente
            existing.update_from_bitbucket_data(project_data)
            logger.debug(
                "Proyecto actualizado",
                project_id=existing.id,
                key=existing.key
            )
            return existing
        else:
            # Crear nuevo
            new_project = Project.from_bitbucket_data(project_data, workspace_id)
            self.add(new_project)
            self.commit()
            logger.info(
                "Nuevo proyecto creado",
                project_id=new_project.id,
                key=new_project.key,
                name=new_project.name,
                workspace_id=workspace_id
            )
            return new_project
    
    def update_metrics(
        self,
        project_id: int,
        total_repos: int,
        total_commits: int,
        total_prs: int
    ) -> None:
        """Actualizar métricas del proyecto"""
        project = self.get_by_id(project_id)
        if project:
            project.update_metrics(total_repos, total_commits, total_prs)
            self.commit()
            logger.debug(
                "Métricas del proyecto actualizadas",
                project_id=project_id,
                total_repos=total_repos,
                total_commits=total_commits,
                total_prs=total_prs
            )


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
    
    def get_by_compliance_score_range(
        self,
        min_score: float,
        max_score: float
    ) -> List[Repository]:
        """Obtener repositorios por rango de score de cumplimiento DevOps"""
        return self.session.query(Repository).filter(
            and_(
                Repository.devops_compliance_score >= min_score,
                Repository.devops_compliance_score <= max_score
            )
        ).all()
    
    def get_low_compliance_repositories(self, threshold: float = 50.0) -> List[Repository]:
        """Obtener repositorios con bajo cumplimiento DevOps"""
        return self.session.query(Repository).filter(
            Repository.devops_compliance_score < threshold
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
        
        if existing:
            # Actualizar existente
            existing.update_from_bitbucket_data(repository_data)
            logger.debug(
                "Repositorio actualizado",
                repository_id=existing.id,
                slug=existing.slug
            )
            return existing
        else:
            # Crear nuevo
            new_repository = Repository.from_bitbucket_data(
                repository_data, workspace_id, project_id
            )
            self.add(new_repository)
            self.commit()
            logger.info(
                "Nuevo repositorio creado",
                repository_id=new_repository.id,
                slug=new_repository.slug,
                name=new_repository.name,
                workspace_id=workspace_id,
                project_id=project_id
            )
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
            logger.debug(
                "Cumplimiento DevOps del repositorio actualizado",
                repository_id=repository_id,
                compliance_data=compliance_data
            )
    
    def get_repository_summary(self, repository_id: int) -> Optional[Dict[str, Any]]:
        """Obtener resumen completo del repositorio"""
        repository = self.get_by_id(repository_id)
        if not repository:
            return None
        
        # Contar commits y pull requests
        commits_count = self.session.query(Commit).filter(
            Commit.repository_id == repository_id
        ).count()
        
        pull_requests_count = self.session.query(PullRequest).filter(
            PullRequest.repository_id == repository_id
        ).count()
        
        open_pull_requests_count = self.session.query(PullRequest).filter(
            and_(
                PullRequest.repository_id == repository_id,
                PullRequest.state == 'OPEN'
            )
        ).count()
        
        return {
            'id': repository.id,
            'name': repository.name,
            'slug': repository.slug,
            'language': repository.language,
            'is_private': repository.is_private,
            'size_bytes': repository.size_bytes,
            'total_commits': commits_count,
            'total_pull_requests': pull_requests_count,
            'open_pull_requests': open_pull_requests_count,
            'devops_compliance': repository.get_devops_compliance_summary(),
            'last_activity': repository.last_activity_date.isoformat() if repository.last_activity_date else None,
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
            logger.debug(
                "Commit actualizado",
                commit_id=existing.id,
                hash=existing.hash[:8]
            )
            return existing
        else:
            # Crear nuevo
            new_commit = Commit.from_bitbucket_data(commit_data, repository_id)
            self.add(new_commit)
            self.commit()
            logger.debug(
                "Nuevo commit creado",
                commit_id=new_commit.id,
                hash=new_commit.hash[:8],
                repository_id=repository_id
            )
            return new_commit
    
    def get_commit_statistics(self, repository_id: int) -> Dict[str, Any]:
        """Obtener estadísticas de commits de un repositorio"""
        stats = self.session.query(
            func.count(Commit.id).label('total_commits'),
            func.sum(Commit.additions).label('total_additions'),
            func.sum(Commit.deletions).label('total_deletions'),
            func.sum(Commit.total_changes).label('total_changes'),
            func.avg(Commit.additions).label('avg_additions'),
            func.avg(Commit.deletions).label('avg_deletions'),
            func.avg(Commit.total_changes).label('avg_changes')
        ).filter(Commit.repository_id == repository_id).first()
        
        return {
            'total_commits': stats.total_commits or 0,
            'total_additions': stats.total_additions or 0,
            'total_deletions': stats.total_deletions or 0,
            'total_changes': stats.total_changes or 0,
            'avg_additions': float(stats.avg_additions or 0),
            'avg_deletions': float(stats.avg_deletions or 0),
            'avg_changes': float(stats.avg_changes or 0)
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
            logger.debug(
                "Pull request actualizado",
                pr_id=existing.id,
                bitbucket_id=existing.bitbucket_id
            )
            return existing
        else:
            # Crear nuevo
            new_pr = PullRequest.from_bitbucket_data(pr_data, repository_id)
            self.add(new_pr)
            self.commit()
            logger.info(
                "Nuevo pull request creado",
                pr_id=new_pr.id,
                bitbucket_id=new_pr.bitbucket_id,
                title=new_pr.title,
                repository_id=repository_id
            )
            return new_pr
    
    def get_pull_request_statistics(self, repository_id: int) -> Dict[str, Any]:
        """Obtener estadísticas de pull requests de un repositorio"""
        stats = self.session.query(
            func.count(PullRequest.id).label('total_prs'),
            func.sum(PullRequest.additions).label('total_additions'),
            func.sum(PullRequest.deletions).label('total_deletions'),
            func.sum(PullRequest.total_changes).label('total_changes'),
            func.avg(PullRequest.additions).label('avg_additions'),
            func.avg(PullRequest.deletions).label('avg_deletions'),
            func.avg(PullRequest.total_changes).label('avg_changes')
        ).filter(PullRequest.repository_id == repository_id).first()
        
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
        
        return {
            'total_prs': stats.total_prs or 0,
            'open_prs': open_count,
            'merged_prs': merged_count,
            'declined_prs': declined_count,
            'total_additions': stats.total_additions or 0,
            'total_deletions': stats.total_deletions or 0,
            'total_changes': stats.total_changes or 0,
            'avg_additions': float(stats.avg_additions or 0),
            'avg_deletions': float(stats.avg_deletions or 0),
            'avg_changes': float(stats.avg_changes or 0)
        }
