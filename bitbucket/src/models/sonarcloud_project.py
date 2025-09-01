"""
Modelo para SonarCloudProject de SonarCloud
"""

from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from .base import Base
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SonarCloudProject(Base):
    """
    Modelo para representar un Proyecto de SonarCloud
    
    Un proyecto de SonarCloud es equivalente a un repositorio en Bitbucket
    """
    
    __tablename__ = 'sonarcloud_projects'
    
    # Campos de identificación
    key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Campos de información
    description = Column(Text, nullable=True)
    visibility = Column(String(50), nullable=True)  # public, private
    
    # Campos de metadatos de SonarCloud
    sonarcloud_id = Column(String(100), unique=True, nullable=True)
    qualifier = Column(String(50), nullable=True)  # TRK, APP, etc.
    
    # Campos de enlaces SCM (para relacionar con Bitbucket)
    scm_url = Column(String(500), nullable=True)  # URL del repositorio SCM
    scm_provider = Column(String(50), nullable=True)  # git, svn, etc.
    
    # Campos de análisis
    last_analysis_date = Column(DateTime(), nullable=True)
    revision = Column(String(100), nullable=True)
    
    # Relación con Organization
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    organization = relationship("Organization", back_populates="sonarcloud_projects")
    
    # Relación con Repository de Bitbucket (opcional, basada en scm_url)
    bitbucket_repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=True)
    bitbucket_repository = relationship("Repository", foreign_keys=[bitbucket_repository_id])
    
    # Relación con Issues
    issues = relationship("Issue", back_populates="sonarcloud_project", cascade="all, delete-orphan")
    
    # Relación con Security Hotspots
    security_hotspots = relationship("SecurityHotspot", back_populates="sonarcloud_project", cascade="all, delete-orphan")
    
    # Relación con Quality Gates
    quality_gates = relationship("QualityGate", back_populates="sonarcloud_project", cascade="all, delete-orphan")
    
    # Relación con Metrics
    metrics = relationship("Metric", back_populates="sonarcloud_project", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """Representación string del proyecto"""
        return f"<SonarCloudProject(key='{self.key}', name='{self.name}')>"
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict, organization_id: int) -> 'SonarCloudProject':
        """
        Crear instancia de SonarCloudProject desde datos de la API de SonarCloud
        
        Args:
            data: Datos del proyecto desde la API
            organization_id: ID de la organización al que pertenece
            
        Returns:
            SonarCloudProject: Nueva instancia del proyecto
        """
        # Campos SCM básicos (sin extracción compleja)
        scm_url = None
        scm_provider = None
        
        # Convertir fecha ISO a datetime si existe
        last_analysis_date = None
        if data.get('lastAnalysisDate'):
            try:
                from datetime import datetime
                # Remover la zona horaria para SQL Server
                date_str = data['lastAnalysisDate'].split('+')[0].split('Z')[0]
                last_analysis_date = datetime.fromisoformat(date_str)
            except (ValueError, AttributeError):
                last_analysis_date = None
        
        return cls(
            key=data.get('key'),
            name=data.get('name'),
            description=data.get('description'),
            visibility=data.get('visibility'),
            sonarcloud_id=data.get('id') or data.get('key'),
            qualifier=data.get('qualifier'),
            scm_url=scm_url,
            scm_provider=scm_provider,
            last_analysis_date=last_analysis_date,
            revision=data.get('revision'),
            organization_id=organization_id
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar proyecto desde datos de la API de SonarCloud
        
        Args:
            data: Datos del proyecto desde la API
        """
        self.name = data.get('name', self.name)
        self.description = data.get('description', self.description)
        self.visibility = data.get('visibility', self.visibility)
        self.qualifier = data.get('qualifier', self.qualifier)
        # No actualizar campos SCM por ahora
        
        # Actualizar fecha de análisis
        if data.get('lastAnalysisDate'):
            try:
                from datetime import datetime
                date_str = data['lastAnalysisDate'].split('+')[0].split('Z')[0]
                self.last_analysis_date = datetime.fromisoformat(date_str)
            except (ValueError, AttributeError):
                pass  # Mantener la fecha anterior si hay error
        self.revision = data.get('revision', self.revision)
