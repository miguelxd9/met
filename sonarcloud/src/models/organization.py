"""
Modelo para organizaciones de SonarCloud
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import relationship

from .base import Base


class Organization(Base):
    """
    Modelo para organizaciones de SonarCloud
    
    Representa una organización en SonarCloud con sus propiedades
    y métricas asociadas.
    """
    
    __tablename__ = 'organizations'
    
    # Campos de identificación
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Campos de SonarCloud
    sonarcloud_id = Column(String(255), unique=True, nullable=False, index=True)
    avatar_url = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)
    
    # Campos de configuración
    is_private = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Campos de métricas
    total_projects = Column(Integer, default=0, nullable=False)
    total_quality_gates = Column(Integer, default=0, nullable=False)
    total_issues = Column(Integer, default=0, nullable=False)
    total_security_hotspots = Column(Integer, default=0, nullable=False)
    
    # Campos de fechas
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relaciones
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    quality_gates = relationship("QualityGate", back_populates="organization", cascade="all, delete-orphan")
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict) -> 'Organization':
        """
        Crear instancia desde datos de la API de SonarCloud
        
        Args:
            data: Datos de la organización desde SonarCloud
            
        Returns:
            Organization: Instancia de la organización
        """
        import uuid as uuid_lib
        
        return cls(
            uuid=str(uuid_lib.uuid4()),
            key=data.get('key'),
            name=data.get('name'),
            description=data.get('description'),
            sonarcloud_id=data.get('id'),
            avatar_url=data.get('avatar'),
            url=data.get('url'),
            is_private=data.get('private', True),
            is_default=data.get('default', False),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar organización desde datos de la API de SonarCloud
        
        Args:
            data: Datos de la organización desde SonarCloud
        """
        self.name = data.get('name', self.name)
        self.description = data.get('description', self.description)
        self.avatar_url = data.get('avatar', self.avatar_url)
        self.url = data.get('url', self.url)
        self.is_private = data.get('private', self.is_private)
        self.is_default = data.get('default', self.is_default)
        self.updated_at = datetime.now()
    
    def update_metrics(
        self,
        total_projects: int = None,
        total_quality_gates: int = None,
        total_issues: int = None,
        total_security_hotspots: int = None
    ) -> None:
        """
        Actualizar métricas de la organización
        
        Args:
            total_projects: Total de proyectos
            total_quality_gates: Total de quality gates
            total_issues: Total de issues
            total_security_hotspots: Total de security hotspots
        """
        if total_projects is not None:
            self.total_projects = total_projects
        if total_quality_gates is not None:
            self.total_quality_gates = total_quality_gates
        if total_issues is not None:
            self.total_issues = total_issues
        if total_security_hotspots is not None:
            self.total_security_hotspots = total_security_hotspots
        self.updated_at = datetime.now()
    
    def get_metrics_summary(self) -> dict:
        """
        Obtener resumen de métricas de la organización
        
        Returns:
            dict: Resumen de métricas
        """
        return {
            'total_projects': self.total_projects,
            'total_quality_gates': self.total_quality_gates,
            'total_issues': self.total_issues,
            'total_security_hotspots': self.total_security_hotspots
        }
    
    def __repr__(self) -> str:
        return f"<Organization(key='{self.key}', name='{self.name}')>"
