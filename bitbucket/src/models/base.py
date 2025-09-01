"""
Modelo base para todos los modelos de la base de datos
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


class BaseModel:
    """
    Modelo base con campos comunes para todos los modelos
    
    Incluye:
    - ID autoincremental
    - Timestamps de creación y actualización
    - Métodos de utilidad
    """
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(), server_default=func.getdate(), nullable=False)
    updated_at = Column(DateTime(), server_default=func.getdate(), onupdate=func.getdate(), nullable=False)
    
    def to_dict(self) -> dict:
        """
        Convertir modelo a diccionario
        
        Returns:
            dict: Representación en diccionario del modelo
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    def update_from_dict(self, data: dict) -> None:
        """
        Actualizar modelo desde diccionario
        
        Args:
            data: Diccionario con datos a actualizar
        """
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'updated_at']:
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """Representación string del modelo"""
        return f"<{self.__class__.__name__}(id={self.id})>"


# Crear base declarativa
Base = declarative_base(cls=BaseModel)
