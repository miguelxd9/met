"""
Modelo para métricas de SonarCloud
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Metric(Base):
    """
    Modelo para métricas de SonarCloud
    
    Representa una métrica específica de un proyecto con su valor
    y metadatos asociados.
    """
    
    __tablename__ = 'metrics'
    
    # Campos de identificación
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    key = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Campos de SonarCloud
    sonarcloud_id = Column(String(255), unique=True, nullable=False, index=True)
    project_key = Column(String(255), nullable=False, index=True)
    
    # Campos de valor
    value = Column(Float, nullable=True)
    string_value = Column(String(500), nullable=True)
    data_type = Column(String(50), nullable=False, default='FLOAT')  # FLOAT, INT, STRING, BOOL
    
    # Campos de metadatos
    domain = Column(String(100), nullable=True)  # Coverage, Duplications, etc.
    direction = Column(Integer, default=0, nullable=False)  # -1: mejor menor, 0: neutral, 1: mejor mayor
    qualitative = Column(String(50), nullable=True)  # BETTER, WORSE
    
    # Campos de fechas
    measured_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relaciones
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    project = relationship("Project", back_populates="metrics")
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict, project_id: int) -> 'Metric':
        """
        Crear instancia desde datos de la API de SonarCloud
        
        Args:
            data: Datos de la métrica desde SonarCloud
            project_id: ID del proyecto
            
        Returns:
            Metric: Instancia de la métrica
        """
        import uuid as uuid_lib
        
        # Parsear fecha de medición
        measured_at = None
        if data.get('date'):
            try:
                measured_at = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            except:
                pass
        
        # Determinar tipo de dato
        data_type = 'FLOAT'
        if isinstance(data.get('value'), int):
            data_type = 'INT'
        elif isinstance(data.get('value'), str):
            data_type = 'STRING'
        elif isinstance(data.get('value'), bool):
            data_type = 'BOOL'
        
        return cls(
            uuid=str(uuid_lib.uuid4()),
            key=data.get('metric'),
            name=data.get('metric'),
            description=data.get('description'),
            sonarcloud_id=data.get('id'),
            project_key=data.get('projectKey'),
            value=float(data.get('value', 0)) if data.get('value') is not None else None,
            string_value=str(data.get('value')) if isinstance(data.get('value'), str) else None,
            data_type=data_type,
            domain=data.get('domain'),
            direction=data.get('direction', 0),
            qualitative=data.get('qualitative'),
            measured_at=measured_at,
            project_id=project_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar métrica desde datos de la API de SonarCloud
        
        Args:
            data: Datos de la métrica desde SonarCloud
        """
        self.name = data.get('metric', self.name)
        self.description = data.get('description', self.description)
        self.domain = data.get('domain', self.domain)
        self.direction = data.get('direction', self.direction)
        self.qualitative = data.get('qualitative', self.qualitative)
        
        # Actualizar valor
        value = data.get('value')
        if value is not None:
            if isinstance(value, (int, float)):
                self.value = float(value)
                self.string_value = None
            else:
                self.value = None
                self.string_value = str(value)
        
        # Parsear fecha de medición
        if data.get('date'):
            try:
                self.measured_at = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            except:
                pass
        
        self.updated_at = datetime.now()
    
    def get_value(self) -> any:
        """
        Obtener el valor de la métrica en el tipo correcto
        
        Returns:
            any: Valor de la métrica
        """
        if self.data_type == 'STRING':
            return self.string_value
        elif self.data_type == 'BOOL':
            return bool(self.value) if self.value is not None else None
        else:
            return self.value
    
    def get_formatted_value(self) -> str:
        """
        Obtener el valor formateado de la métrica
        
        Returns:
            str: Valor formateado
        """
        value = self.get_value()
        if value is None:
            return 'N/A'
        
        if self.data_type == 'FLOAT':
            return f"{value:.2f}"
        elif self.data_type == 'INT':
            return f"{int(value)}"
        else:
            return str(value)
    
    def is_better_than(self, other_value: any) -> bool:
        """
        Comparar si el valor actual es mejor que otro valor
        
        Args:
            other_value: Valor a comparar
            
        Returns:
            bool: True si es mejor, False en caso contrario
        """
        if self.value is None or other_value is None:
            return False
        
        if self.direction == 1:  # Mayor es mejor
            return self.value > other_value
        elif self.direction == -1:  # Menor es mejor
            return self.value < other_value
        else:
            return False
    
    def get_summary(self) -> dict:
        """
        Obtener resumen de la métrica
        
        Returns:
            dict: Resumen de la métrica
        """
        return {
            'key': self.key,
            'name': self.name,
            'value': self.get_value(),
            'formatted_value': self.get_formatted_value(),
            'data_type': self.data_type,
            'domain': self.domain,
            'direction': self.direction,
            'qualitative': self.qualitative,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None
        }
    
    def __repr__(self) -> str:
        return f"<Metric(key='{self.key}', value='{self.get_formatted_value()}')>"
