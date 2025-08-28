"""
Modelo para Quality Gates de SonarCloud
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class QualityGate(Base):
    """
    Modelo para Quality Gates de SonarCloud
    
    Representa un Quality Gate de un proyecto con sus condiciones
    y resultados de evaluación.
    """
    
    __tablename__ = 'quality_gates'
    
    # Campos de identificación
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Campos de SonarCloud
    sonarcloud_id = Column(String(255), unique=True, nullable=False, index=True)
    project_key = Column(String(255), nullable=False, index=True)
    
    # Campos de configuración
    is_default = Column(Boolean, default=False, nullable=False)
    is_built_in = Column(Boolean, default=False, nullable=False)
    
    # Campos de evaluación
    status = Column(String(50), nullable=True)  # PASSED, FAILED, WARN
    evaluated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Campos de fechas
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relaciones
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    organization = relationship("Organization", back_populates="quality_gates")
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    project = relationship("Project", back_populates="quality_gates")
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict, organization_id: int, project_id: int) -> 'QualityGate':
        """
        Crear instancia desde datos de la API de SonarCloud
        
        Args:
            data: Datos del Quality Gate desde SonarCloud
            organization_id: ID de la organización
            project_id: ID del proyecto
            
        Returns:
            QualityGate: Instancia del Quality Gate
        """
        import uuid as uuid_lib
        
        # Parsear fecha de evaluación
        evaluated_at = None
        if data.get('evaluatedAt'):
            try:
                evaluated_at = datetime.fromisoformat(data['evaluatedAt'].replace('Z', '+00:00'))
            except:
                pass
        
        return cls(
            uuid=str(uuid_lib.uuid4()),
            name=data.get('name'),
            description=data.get('description'),
            sonarcloud_id=data.get('id'),
            project_key=data.get('projectKey'),
            is_default=data.get('default', False),
            is_built_in=data.get('builtIn', False),
            status=data.get('status'),
            evaluated_at=evaluated_at,
            organization_id=organization_id,
            project_id=project_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar Quality Gate desde datos de la API de SonarCloud
        
        Args:
            data: Datos del Quality Gate desde SonarCloud
        """
        self.name = data.get('name', self.name)
        self.description = data.get('description', self.description)
        self.is_default = data.get('default', self.is_default)
        self.is_built_in = data.get('builtIn', self.is_built_in)
        self.status = data.get('status', self.status)
        
        # Parsear fecha de evaluación
        if data.get('evaluatedAt'):
            try:
                self.evaluated_at = datetime.fromisoformat(data['evaluatedAt'].replace('Z', '+00:00'))
            except:
                pass
        
        self.updated_at = datetime.now()
    
    def is_passed(self) -> bool:
        """
        Verificar si el Quality Gate pasó
        
        Returns:
            bool: True si pasó, False en caso contrario
        """
        return self.status == 'PASSED'
    
    def is_failed(self) -> bool:
        """
        Verificar si el Quality Gate falló
        
        Returns:
            bool: True si falló, False en caso contrario
        """
        return self.status == 'FAILED'
    
    def is_warning(self) -> bool:
        """
        Verificar si el Quality Gate está en advertencia
        
        Returns:
            bool: True si está en advertencia, False en caso contrario
        """
        return self.status == 'WARN'
    
    def get_status_summary(self) -> dict:
        """
        Obtener resumen del estado del Quality Gate
        
        Returns:
            dict: Resumen del estado
        """
        return {
            'status': self.status,
            'is_passed': self.is_passed(),
            'is_failed': self.is_failed(),
            'is_warning': self.is_warning(),
            'evaluated_at': self.evaluated_at.isoformat() if self.evaluated_at else None,
            'is_default': self.is_default,
            'is_built_in': self.is_built_in
        }
    
    def __repr__(self) -> str:
        return f"<QualityGate(name='{self.name}', status='{self.status}')>"
