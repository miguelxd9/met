"""
Modelo para Commit de Bitbucket
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from .base import Base


class Commit(Base):
    """
    Modelo para representar un Commit de Bitbucket
    
    Un commit representa un cambio en el código fuente
    """
    
    __tablename__ = 'commits'
    
    # Campos de identificación
    hash = Column(String(40), unique=True, nullable=False, index=True)
    bitbucket_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Campos de información
    message = Column(Text, nullable=False)
    author_name = Column(String(255), nullable=False)
    author_email = Column(String(255), nullable=False)
    
    # Campos de metadatos
    commit_date = Column(DateTime(timezone=True), nullable=False)
    author_date = Column(DateTime(timezone=True), nullable=False)
    
    # Campos de metadatos de Bitbucket
    is_merge_commit = Column(Boolean, default=False, nullable=False)
    
    # Relación con Repository
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    repository = relationship("Repository", back_populates="commits")
    
    def __repr__(self) -> str:
        """Representación string del commit"""
        return f"<Commit(hash='{self.hash[:8]}', message='{self.message[:50]}...')>"
    
    @classmethod
    def from_bitbucket_data(cls, data: dict, repository_id: int) -> 'Commit':
        """
        Crear instancia de Commit desde datos de la API de Bitbucket
        
        Args:
            data: Datos del commit desde la API
            repository_id: ID del repositorio al que pertenece
            
        Returns:
            Commit: Nueva instancia del commit
        """
        # Parsear fechas con manejo de valores vacíos
        commit_date_str = data.get('date', '')
        author_date_str = data.get('author_date', '')
        
        commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00')) if commit_date_str else datetime.now(timezone.utc)
        author_date = datetime.fromisoformat(author_date_str.replace('Z', '+00:00')) if author_date_str else datetime.now(timezone.utc)
        
        # Usar el hash como bitbucket_id si el campo 'id' no está disponible
        bitbucket_id = data.get('id') or data.get('hash', '')
        
        return cls(
            hash=data.get('hash'),
            bitbucket_id=bitbucket_id,
            message=data.get('message', ''),
            author_name=data.get('author', {}).get('raw', ''),
            author_email=data.get('author', {}).get('user', {}).get('email', ''),
            commit_date=commit_date,
            author_date=author_date,
            is_merge_commit=data.get('is_merge_commit', False),
            repository_id=repository_id
        )
    
    def update_from_bitbucket_data(self, data: dict) -> None:
        """
        Actualizar commit desde datos de la API de Bitbucket
        
        Args:
            data: Datos del commit desde la API
        """
        self.message = data.get('message', self.message)
        self.author_name = data.get('author', {}).get('raw', self.author_name)
        self.author_email = data.get('author', {}).get('user', {}).get('email', self.author_email)
        
        # Actualizar metadatos
        self.is_merge_commit = data.get('is_merge_commit', self.is_merge_commit)
    

    
    def get_change_summary(self) -> dict:
        """
        Obtener resumen del commit
        
        Returns:
            dict: Resumen del commit
        """
        return {
            'hash': self.hash,
            'message': self.message,
            'author': self.author_name,
            'date': self.commit_date.isoformat(),
            'is_merge': self.is_merge_commit
        }
