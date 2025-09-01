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
    
    # Campos de metadatos de Bitbucket
    size_bytes = Column(BigInteger, default=0, nullable=False)
    

    
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
            size_bytes=data.get('size', 0)
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
        
        # Actualizar metadatos básicos
        self.size_bytes = data.get('size', self.size_bytes)
    

    

    

