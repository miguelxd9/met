"""
Modelo para Organization de SonarCloud
"""

from sqlalchemy import Column, String, Boolean, Text, Integer
from sqlalchemy.orm import relationship

from .base import Base


class Organization(Base):
    """
    Modelo para representar una Organization de SonarCloud
    
    Una organización agrupa proyectos relacionados (equivalente a workspace en Bitbucket)
    """
    
    __tablename__ = 'organizations'
    
    # Campos de identificación
    key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Campos de información
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    
    # Campos de metadatos de SonarCloud
    sonarcloud_id = Column(String(100), unique=True, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Relación con Proyectos de SonarCloud
    sonarcloud_projects = relationship("SonarCloudProject", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """Representación string de la organización"""
        return f"<Organization(key='{self.key}', name='{self.name}')>"
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict) -> 'Organization':
        """
        Crear instancia de Organization desde datos de la API de SonarCloud
        
        Args:
            data: Datos de la organización desde la API
            
        Returns:
            Organization: Nueva instancia de la organización
        """
        return cls(
            key=data.get('key'),
            name=data.get('name'),
            description=data.get('description'),
            url=data.get('url'),
            sonarcloud_id=data.get('id') or data.get('key'),
            avatar_url=data.get('avatar')
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar organización desde datos de la API de SonarCloud
        
        Args:
            data: Datos de la organización desde la API
        """
        self.name = data.get('name', self.name)
        self.description = data.get('description', self.description)
        self.url = data.get('url', self.url)
        self.avatar_url = data.get('avatar', self.avatar_url)
