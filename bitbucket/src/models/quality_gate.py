"""
Modelo para QualityGate de SonarCloud
"""

from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base


class QualityGateStatus(enum.Enum):
    """Enumeración para estado de quality gates"""
    OK = "OK"
    WARN = "WARN"
    ERROR = "ERROR"


class QualityGate(Base):
    """
    Modelo para representar un Quality Gate de SonarCloud
    
    Un quality gate representa el estado de calidad de un proyecto
    """
    
    __tablename__ = 'quality_gates'
    
    # Campos de identificación
    sonarcloud_id = Column(String(100), unique=True, nullable=False, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    
    # Campos de información
    name = Column(String(255), nullable=False)
    status = Column(Enum(QualityGateStatus), nullable=False)
    
    # Campos de metadatos
    conditions_count = Column(Integer, nullable=True)
    ignored_conditions_count = Column(Integer, nullable=True)
    
    # Campos de fechas
    analysis_date = Column(DateTime(), nullable=True)
    
    # Relación con SonarCloudProject
    sonarcloud_project_id = Column(Integer, ForeignKey('sonarcloud_projects.id'), nullable=False)
    sonarcloud_project = relationship("SonarCloudProject", back_populates="quality_gates")
    
    def __repr__(self) -> str:
        """Representación string del quality gate"""
        return f"<QualityGate(key='{self.key}', name='{self.name}', status='{self.status.value}')>"
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict, sonarcloud_project_id: int) -> 'QualityGate':
        """
        Crear instancia de QualityGate desde datos de la API de SonarCloud
        
        Args:
            data: Datos del quality gate desde la API
            sonarcloud_project_id: ID del proyecto de SonarCloud
            
        Returns:
            QualityGate: Nueva instancia del quality gate
        """
        # Generar un ID único si no existe
        sonarcloud_id = data.get('id')
        if not sonarcloud_id:
            # Usar el project_id como base para generar un ID único
            sonarcloud_id = f"qg_{sonarcloud_project_id}_{data.get('status', 'OK')}"
        
        # Generar key si no existe
        key = data.get('key')
        if not key:
            key = f"quality_gate_{sonarcloud_project_id}"
        
        # Generar nombre si no existe
        name = data.get('name')
        if not name:
            name = f"Quality Gate {sonarcloud_project_id}"
        
        return cls(
            sonarcloud_id=sonarcloud_id,
            key=key,
            name=name,
            status=QualityGateStatus(data.get('status', 'OK')),
            conditions_count=data.get('conditionsCount'),
            ignored_conditions_count=data.get('ignoredConditionsCount'),
            analysis_date=data.get('analysisDate'),
            sonarcloud_project_id=sonarcloud_project_id
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar quality gate desde datos de la API de SonarCloud
        
        Args:
            data: Datos del quality gate desde la API
        """
        self.name = data.get('name', self.name)
        self.status = QualityGateStatus(data.get('status', self.status.value))
        self.conditions_count = data.get('conditionsCount', self.conditions_count)
        self.ignored_conditions_count = data.get('ignoredConditionsCount', self.ignored_conditions_count)
        self.analysis_date = data.get('analysisDate', self.analysis_date)
