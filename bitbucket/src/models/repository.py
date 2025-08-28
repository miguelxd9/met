"""
Modelo para Repository de Bitbucket
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey, DateTime, Float, BigInteger
from sqlalchemy.orm import relationship

from .base import Base


class Repository(Base):
    """
    Modelo para representar un Repository de Bitbucket
    
    Un repositorio es la unidad básica de código fuente
    """
    
    __tablename__ = 'repositories'
    
    # Campos de identificación
    uuid = Column(String(50), unique=True, nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Campos de información
    description = Column(Text, nullable=True)
    is_private = Column(Boolean, default=True, nullable=False)
    language = Column(String(50), nullable=True)
    
    # Campos de metadatos de Bitbucket
    bitbucket_id = Column(String(100), unique=True, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Relaciones
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False)
    workspace = relationship("Workspace", back_populates="repositories")
    
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    project = relationship("Project", back_populates="repositories")
    
    # Relaciones con entidades relacionadas
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="repository", cascade="all, delete-orphan")
    
    # Campos de métricas
    size_bytes = Column(BigInteger, default=0, nullable=False)
    total_commits = Column(Integer, default=0, nullable=False)
    total_branches = Column(Integer, default=0, nullable=False)
    total_tags = Column(Integer, default=0, nullable=False)
    total_pull_requests = Column(Integer, default=0, nullable=False)
    open_pull_requests = Column(Integer, default=0, nullable=False)
    closed_pull_requests = Column(Integer, default=0, nullable=False)
    
    # Campos de actividad
    last_commit_date = Column(DateTime(timezone=True), nullable=True)
    last_pull_request_date = Column(DateTime(timezone=True), nullable=True)
    last_activity_date = Column(DateTime(timezone=True), nullable=True)
    
    # Campos de calidad (para métricas DevOps)
    has_readme = Column(Boolean, default=False, nullable=False)
    has_license = Column(Boolean, default=False, nullable=False)
    has_ci_config = Column(Boolean, default=False, nullable=False)
    has_security_policy = Column(Boolean, default=False, nullable=False)
    has_contributing_guide = Column(Boolean, default=False, nullable=False)
    
    # Score de cumplimiento DevOps (0-100)
    devops_compliance_score = Column(Float, default=0.0, nullable=False)
    
    def __repr__(self) -> str:
        """Representación string del repositorio"""
        return f"<Repository(slug='{self.slug}', name='{self.name}')>"
    
    @classmethod
    def from_bitbucket_data(
        cls, 
        data: dict, 
        workspace_id: int, 
        project_id: int = None
    ) -> 'Repository':
        """
        Crear instancia de Repository desde datos de la API de Bitbucket
        
        Args:
            data: Datos del repositorio desde la API
            workspace_id: ID del workspace al que pertenece
            project_id: ID del proyecto al que pertenece (opcional)
            
        Returns:
            Repository: Nueva instancia del repositorio
        """
        # Limpiar UUID removiendo llaves si las tiene
        uuid = data.get('uuid', '')
        if uuid and uuid.startswith('{') and uuid.endswith('}'):
            uuid = uuid[1:-1]  # Remover llaves
        
        return cls(
            uuid=uuid,
            slug=data.get('slug'),
            name=data.get('name'),
            description=data.get('description'),
            is_private=data.get('is_private', True),
            language=data.get('language'),
            bitbucket_id=data.get('id') or data.get('uuid'),  # Usar uuid como fallback
            avatar_url=data.get('avatar_url'),
            website=data.get('website'),
            workspace_id=workspace_id,
            project_id=project_id,
            size_bytes=data.get('size', 0),
            total_commits=data.get('commits_count', 0),
            total_branches=data.get('branches_count', 0),
            total_tags=data.get('tags_count', 0),
            total_pull_requests=data.get('pull_requests_count', 0),
            open_pull_requests=data.get('open_pull_requests_count', 0),
            closed_pull_requests=data.get('closed_pull_requests_count', 0)
        )
    
    def update_from_bitbucket_data(self, data: dict) -> None:
        """
        Actualizar repositorio desde datos de la API de Bitbucket
        
        Args:
            data: Datos del repositorio desde la API
        """
        self.name = data.get('name', self.name)
        self.description = data.get('description', self.description)
        self.is_private = data.get('is_private', self.is_private)
        self.language = data.get('language', self.language)
        self.avatar_url = data.get('avatar_url', self.avatar_url)
        self.website = data.get('website', self.website)
        
        # Actualizar métricas básicas
        self.size_bytes = data.get('size', self.size_bytes)
        self.total_commits = data.get('commits_count', self.total_commits)
        self.total_branches = data.get('branches_count', self.total_branches)
        self.total_tags = data.get('tags_count', self.total_tags)
        self.total_pull_requests = data.get('pull_requests_count', self.total_pull_requests)
        self.open_pull_requests = data.get('open_pull_requests_count', self.open_pull_requests)
        self.closed_pull_requests = data.get('closed_pull_requests_count', self.closed_pull_requests)
    
    def update_activity_dates(
        self,
        last_commit: datetime = None,
        last_pr: datetime = None,
        last_activity: datetime = None
    ) -> None:
        """
        Actualizar fechas de actividad del repositorio
        
        Args:
            last_commit: Fecha del último commit
            last_pr: Fecha del último pull request
            last_activity: Fecha de la última actividad
        """
        if last_commit:
            self.last_commit_date = last_commit
        
        if last_pr:
            self.last_pull_request_date = last_pr
        
        if last_activity:
            self.last_activity_date = last_activity
        elif last_commit or last_pr:
            # Usar la fecha más reciente como última actividad
            dates = [d for d in [last_commit, last_pr] if d]
            if dates:
                self.last_activity_date = max(dates)
    
    def update_devops_compliance(
        self,
        has_readme: bool = None,
        has_license: bool = None,
        has_ci_config: bool = None,
        has_security_policy: bool = None,
        has_contributing_guide: bool = None
    ) -> None:
        """
        Actualizar métricas de cumplimiento DevOps
        
        Args:
            has_readme: Tiene README
            has_license: Tiene licencia
            has_ci_config: Tiene configuración de CI
            has_security_policy: Tiene política de seguridad
            has_contributing_guide: Tiene guía de contribución
        """
        if has_readme is not None:
            self.has_readme = has_readme
        if has_license is not None:
            self.has_license = has_license
        if has_ci_config is not None:
            self.has_ci_config = has_ci_config
        if has_security_policy is not None:
            self.has_security_policy = has_security_policy
        if has_contributing_guide is not None:
            self.has_contributing_guide = has_contributing_guide
        
        # Calcular score de cumplimiento (0-100)
        compliance_items = [
            self.has_readme,
            self.has_license,
            self.has_ci_config,
            self.has_security_policy,
            self.has_contributing_guide
        ]
        
        score = sum(compliance_items) / len(compliance_items) * 100
        self.devops_compliance_score = score
    
    def get_devops_compliance_summary(self) -> dict:
        """
        Obtener resumen de cumplimiento DevOps
        
        Returns:
            dict: Resumen de cumplimiento DevOps
        """
        return {
            'total_score': self.devops_compliance_score,
            'has_readme': self.has_readme,
            'has_license': self.has_license,
            'has_ci_config': self.has_ci_config,
            'has_security_policy': self.has_security_policy,
            'has_contributing_guide': self.has_contributing_guide,
            'compliance_level': self._get_compliance_level()
        }
    
    def _get_compliance_level(self) -> str:
        """
        Obtener nivel de cumplimiento DevOps
        
        Returns:
            str: Nivel de cumplimiento (Low, Medium, High, Excellent)
        """
        if self.devops_compliance_score >= 90:
            return "Excellent"
        elif self.devops_compliance_score >= 70:
            return "High"
        elif self.devops_compliance_score >= 50:
            return "Medium"
        else:
            return "Low"
