"""
Modelo para SecurityHotspot de SonarCloud
"""

from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base


class SecurityHotspotStatus(enum.Enum):
    """Enumeración para estado de security hotspots"""
    TO_REVIEW = "TO_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    REVIEWED = "REVIEWED"


class SecurityHotspotResolution(enum.Enum):
    """Enumeración para resolución de security hotspots"""
    SAFE = "SAFE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FIXED = "FIXED"


class SecurityHotspot(Base):
    """
    Modelo para representar un Security Hotspot de SonarCloud
    
    Un security hotspot representa un punto de seguridad que requiere revisión
    """
    
    __tablename__ = 'security_hotspots'
    
    # Campos de identificación
    sonarcloud_id = Column(String(100), unique=True, nullable=False, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    
    # Campos de información
    rule = Column(String(100), nullable=False)  # Regla de seguridad
    status = Column(Enum(SecurityHotspotStatus), nullable=False)
    resolution = Column(Enum(SecurityHotspotResolution), nullable=True)
    
    # Campos de ubicación
    component = Column(String(500), nullable=True)  # Archivo/componente afectado
    line = Column(Integer, nullable=True)  # Línea del código
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    
    # Campos de mensaje
    message = Column(Text, nullable=False)
    
    # Campos de metadatos
    effort = Column(String(50), nullable=True)  # Esfuerzo para resolver
    debt = Column(String(50), nullable=True)  # Deuda técnica
    
    # Campos de fechas
    creation_date = Column(DateTime(), nullable=True)
    update_date = Column(DateTime(), nullable=True)
    
    # Campos de autor
    author = Column(String(200), nullable=True)
    assignee = Column(String(200), nullable=True)
    
    # Relación con SonarCloudProject
    sonarcloud_project_id = Column(Integer, ForeignKey('sonarcloud_projects.id'), nullable=False)
    sonarcloud_project = relationship("SonarCloudProject", back_populates="security_hotspots")
    
    def __repr__(self) -> str:
        """Representación string del security hotspot"""
        return f"<SecurityHotspot(key='{self.key}', rule='{self.rule}', status='{self.status.value}')>"
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict, sonarcloud_project_id: int) -> 'SecurityHotspot':
        """
        Crear instancia de SecurityHotspot desde datos de la API de SonarCloud
        
        Args:
            data: Datos del security hotspot desde la API
            sonarcloud_project_id: ID del proyecto de SonarCloud
            
        Returns:
            SecurityHotspot: Nueva instancia del security hotspot
        """
        return cls(
            sonarcloud_id=data.get('id'),
            key=data.get('key'),
            rule=data.get('rule'),
            status=SecurityHotspotStatus(data.get('status', 'TO_REVIEW')),
            resolution=SecurityHotspotResolution(data.get('resolution')) if data.get('resolution') else None,
            component=data.get('component'),
            line=data.get('line'),
            start_line=data.get('startLine'),
            end_line=data.get('endLine'),
            start_offset=data.get('startOffset'),
            end_offset=data.get('endOffset'),
            message=data.get('message'),
            effort=data.get('effort'),
            debt=data.get('debt'),
            creation_date=data.get('creationDate'),
            update_date=data.get('updateDate'),
            author=data.get('author'),
            assignee=data.get('assignee'),
            sonarcloud_project_id=sonarcloud_project_id
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar security hotspot desde datos de la API de SonarCloud
        
        Args:
            data: Datos del security hotspot desde la API
        """
        self.rule = data.get('rule', self.rule)
        self.status = SecurityHotspotStatus(data.get('status', self.status.value))
        self.resolution = SecurityHotspotResolution(data.get('resolution')) if data.get('resolution') else self.resolution
        self.component = data.get('component', self.component)
        self.line = data.get('line', self.line)
        self.start_line = data.get('startLine', self.start_line)
        self.end_line = data.get('endLine', self.end_line)
        self.start_offset = data.get('startOffset', self.start_offset)
        self.end_offset = data.get('endOffset', self.end_offset)
        self.message = data.get('message', self.message)
        self.effort = data.get('effort', self.effort)
        self.debt = data.get('debt', self.debt)
        self.creation_date = data.get('creationDate', self.creation_date)
        self.update_date = data.get('updateDate', self.update_date)
        self.author = data.get('author', self.author)
        self.assignee = data.get('assignee', self.assignee)
