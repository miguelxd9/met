"""
Modelo para Project de Bitbucket
"""

from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Project(Base):
    """
    Modelo para representar un Project de Bitbucket
    
    Un proyecto agrupa repositorios relacionados dentro de un workspace
    """
    
    __tablename__ = 'projects'
    
    # Campos de identificación
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    key = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Campos de información
    description = Column(Text, nullable=True)
    is_private = Column(Boolean, default=True, nullable=False)
    
    # Campos de metadatos de Bitbucket
    bitbucket_id = Column(String(100), unique=True, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Relación con Workspace
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False)
    workspace = relationship("Workspace", back_populates="projects")
    
    # Relación con Repositorios
    repositories = relationship("Repository", back_populates="project", cascade="all, delete-orphan")
    
    # Campos de métricas
    total_repositories = Column(Integer, default=0, nullable=False)
    total_commits = Column(Integer, default=0, nullable=False)
    total_pull_requests = Column(Integer, default=0, nullable=False)
    
    def __repr__(self) -> str:
        """Representación string del proyecto"""
        return f"<Project(key='{self.key}', name='{self.name}')>"
    
    @classmethod
    def from_bitbucket_data(cls, data: dict, workspace_id: int) -> 'Project':
        """
        Crear instancia de Project desde datos de la API de Bitbucket
        
        Args:
            data: Datos del proyecto desde la API
            workspace_id: ID del workspace al que pertenece
            
        Returns:
            Project: Nueva instancia del proyecto
        """
        # Limpiar UUID removiendo llaves si las tiene
        uuid = data.get('uuid', '')
        if uuid and uuid.startswith('{') and uuid.endswith('}'):
            uuid = uuid[1:-1]  # Remover llaves
        
        return cls(
            uuid=uuid,
            key=data.get('key'),
            name=data.get('name'),
            description=data.get('description'),
            is_private=data.get('is_private', True),
            bitbucket_id=data.get('id') or data.get('uuid'),  # Usar uuid como fallback
            avatar_url=data.get('avatar_url'),
            workspace_id=workspace_id
        )
    
    def update_from_bitbucket_data(self, data: dict) -> None:
        """
        Actualizar proyecto desde datos de la API de Bitbucket
        
        Args:
            data: Datos del proyecto desde la API
        """
        self.name = data.get('name', self.name)
        self.description = data.get('description', self.description)
        self.is_private = data.get('is_private', self.is_private)
        self.avatar_url = data.get('avatar_url', self.avatar_url)
    
    def update_metrics(self, total_repos: int, total_commits: int, total_prs: int) -> None:
        """
        Actualizar métricas del proyecto
        
        Args:
            total_repos: Total de repositorios
            total_commits: Total de commits
            total_prs: Total de pull requests
        """
        self.total_repositories = total_repos
        self.total_commits = total_commits
        self.total_pull_requests = total_prs
