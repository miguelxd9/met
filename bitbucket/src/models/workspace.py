"""
Modelo para Workspace de Bitbucket
"""

from sqlalchemy import Column, String, Boolean, Text, Integer
from sqlalchemy.orm import relationship

from .base import Base


class Workspace(Base):
    """
    Modelo para representar un Workspace de Bitbucket
    
    Un workspace es el contenedor principal que agrupa proyectos y repositorios
    """
    
    __tablename__ = 'workspaces'
    
    # Campos de identificación
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Campos de información
    is_private = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Campos de metadatos de Bitbucket
    bitbucket_id = Column(String(100), unique=True, nullable=False)
    website = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Campos de métricas
    total_repositories = Column(Integer, default=0, nullable=False)
    total_projects = Column(Integer, default=0, nullable=False)
    total_members = Column(Integer, default=0, nullable=False)
    
    # Relaciones
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")
    repositories = relationship("Repository", back_populates="workspace", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """Representación string del workspace"""
        return f"<Workspace(slug='{self.slug}', name='{self.name}')>"
    
    @classmethod
    def from_bitbucket_data(cls, data: dict) -> 'Workspace':
        """
        Crear instancia de Workspace desde datos de la API de Bitbucket
        
        Args:
            data: Datos del workspace desde la API
            
        Returns:
            Workspace: Nueva instancia del workspace
        """
        return cls(
            uuid=data.get('uuid'),
            slug=data.get('slug'),
            name=data.get('name'),
            is_private=data.get('is_private', True),
            description=data.get('description'),
            bitbucket_id=data.get('id'),
            website=data.get('website'),
            location=data.get('location')
        )
    
    def update_from_bitbucket_data(self, data: dict) -> None:
        """
        Actualizar workspace desde datos de la API de Bitbucket
        
        Args:
            data: Datos del workspace desde la API
        """
        self.name = data.get('name', self.name)
        self.is_private = data.get('is_private', self.is_private)
        self.description = data.get('description', self.description)
        self.website = data.get('website', self.website)
        self.location = data.get('location', self.location)
    
    def update_metrics(self, total_repos: int, total_projects: int, total_members: int) -> None:
        """
        Actualizar métricas del workspace
        
        Args:
            total_repos: Total de repositorios
            total_projects: Total de proyectos
            total_members: Total de miembros
        """
        self.total_repositories = total_repos
        self.total_projects = total_projects
        self.total_members = total_members
