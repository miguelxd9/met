"""
Modelo para Metric de SonarCloud
"""

from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship

from .base import Base


class Metric(Base):
    """
    Modelo para representar una Métrica de SonarCloud
    
    Una métrica representa un valor de medición de calidad del código
    """
    
    __tablename__ = 'metrics'
    
    # Campos de identificación
    key = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Campos de valor
    value = Column(Float, nullable=True)
    formatted_value = Column(String(100), nullable=True)
    
    # Campos de metadatos
    type = Column(String(50), nullable=True)  # INT, FLOAT, PERCENT, BOOL, STRING
    domain = Column(String(50), nullable=True)  # Reliability, Security, Maintainability, etc.
    
    # Campos de fechas
    analysis_date = Column(DateTime(), nullable=True)
    
    # Relación con SonarCloudProject
    sonarcloud_project_id = Column(Integer, ForeignKey('sonarcloud_projects.id'), nullable=False)
    sonarcloud_project = relationship("SonarCloudProject", back_populates="metrics")
    
    def __repr__(self) -> str:
        """Representación string de la métrica"""
        return f"<Metric(key='{self.key}', name='{self.name}', value='{self.value}')>"
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict, sonarcloud_project_id: int) -> 'Metric':
        """
        Crear instancia de Metric desde datos de la API de SonarCloud
        
        Args:
            data: Datos de la métrica desde la API
            sonarcloud_project_id: ID del proyecto de SonarCloud
            
        Returns:
            Metric: Nueva instancia de la métrica
        """
        return cls(
            key=data.get('metric'),
            name=data.get('metric'),
            value=data.get('value'),
            formatted_value=data.get('formattedValue'),
            type=data.get('type'),
            domain=data.get('domain'),
            analysis_date=data.get('date'),
            sonarcloud_project_id=sonarcloud_project_id
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar métrica desde datos de la API de SonarCloud
        
        Args:
            data: Datos de la métrica desde la API
        """
        self.value = data.get('value', self.value)
        self.formatted_value = data.get('formattedValue', self.formatted_value)
        self.type = data.get('type', self.type)
        self.domain = data.get('domain', self.domain)
        self.analysis_date = data.get('date', self.analysis_date)
