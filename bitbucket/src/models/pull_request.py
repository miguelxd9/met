"""
Modelo para PullRequest de Bitbucket
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base


class PullRequestState(enum.Enum):
    """Estados posibles de un Pull Request"""
    OPEN = "OPEN"
    MERGED = "MERGED"
    DECLINED = "DECLINED"
    SUPERSEDED = "SUPERSEDED"


class PullRequest(Base):
    """
    Modelo para representar un PullRequest de Bitbucket
    
    Un pull request representa una solicitud de cambios
    """
    
    __tablename__ = 'pull_requests'
    
    # Campos de identificación
    bitbucket_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    
    # Campos de información
    description = Column(Text, nullable=True)
    state = Column(Enum(PullRequestState), nullable=False, default=PullRequestState.OPEN)
    
    # Campos de metadatos
    created_date = Column(DateTime(timezone=True), nullable=False)
    updated_date = Column(DateTime(timezone=True), nullable=False)
    closed_date = Column(DateTime(timezone=True), nullable=True)
    merged_date = Column(DateTime(timezone=True), nullable=True)
    

    
    # Relación con Repository
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    repository = relationship("Repository", back_populates="pull_requests")
    
    def __repr__(self) -> str:
        """Representación string del pull request"""
        return f"<PullRequest(id='{self.bitbucket_id}', title='{self.title[:50]}...')>"
    
    @classmethod
    def from_bitbucket_data(cls, data: dict, repository_id: int) -> 'PullRequest':
        """
        Crear instancia de PullRequest desde datos de la API de Bitbucket
        
        Args:
            data: Datos del pull request desde la API
            repository_id: ID del repositorio al que pertenece
            
        Returns:
            PullRequest: Nueva instancia del pull request
        """
        # Parsear fechas con manejo de valores vacíos
        created_date_str = data.get('created_on', '')
        updated_date_str = data.get('updated_on', '')
        
        created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00')) if created_date_str else datetime.now(timezone.utc)
        updated_date = datetime.fromisoformat(updated_date_str.replace('Z', '+00:00')) if updated_date_str else datetime.now(timezone.utc)
        
        closed_date = None
        if data.get('closed_on'):
            closed_date = datetime.fromisoformat(data.get('closed_on').replace('Z', '+00:00'))
        
        merged_date = None
        if data.get('merged_on'):
            merged_date = datetime.fromisoformat(data.get('merged_on').replace('Z', '+00:00'))
        
        # Determinar estado
        state = PullRequestState.OPEN
        if data.get('state') == 'MERGED':
            state = PullRequestState.MERGED
        elif data.get('state') == 'DECLINED':
            state = PullRequestState.DECLINED
        elif data.get('state') == 'SUPERSEDED':
            state = PullRequestState.SUPERSEDED
        
        # Usar un valor por defecto si el bitbucket_id no está disponible
        bitbucket_id = data.get('id') or f"pr_{data.get('title', '').replace(' ', '_')[:20]}_{created_date.strftime('%Y%m%d')}"
        
        return cls(
            bitbucket_id=bitbucket_id,
            title=data.get('title', ''),
            description=data.get('description'),
            state=state,
            created_date=created_date,
            updated_date=updated_date,
            closed_date=closed_date,
            merged_date=merged_date,
            
            repository_id=repository_id
        )
    
    def update_from_bitbucket_data(self, data: dict) -> None:
        """
        Actualizar pull request desde datos de la API de Bitbucket
        
        Args:
            data: Datos del pull request desde la API
        """
        self.title = data.get('title', self.title)
        self.description = data.get('description', self.description)
        
        # Actualizar estado si cambió
        if data.get('state'):
            if data.get('state') == 'MERGED':
                self.state = PullRequestState.MERGED
            elif data.get('state') == 'DECLINED':
                self.state = PullRequestState.DECLINED
            elif data.get('state') == 'SUPERSEDED':
                self.state = PullRequestState.SUPERSEDED
            else:
                self.state = PullRequestState.OPEN
        
        # Actualizar fechas
        if data.get('updated_on'):
            self.updated_date = datetime.fromisoformat(data.get('updated_on').replace('Z', '+00:00'))
        
        if data.get('closed_on'):
            self.closed_date = datetime.fromisoformat(data.get('closed_on').replace('Z', '+00:00'))
        
        if data.get('merged_on'):
            self.merged_date = datetime.fromisoformat(data.get('merged_on').replace('Z', '+00:00'))
        

    

    
    def get_summary(self) -> dict:
        """
        Obtener resumen del pull request
        
        Returns:
            dict: Resumen del pull request
        """
        return {
            'id': self.bitbucket_id,
            'title': self.title,
            'state': self.state.value,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat(),
            'closed_date': self.closed_date.isoformat() if self.closed_date else None,
            'merged_date': self.merged_date.isoformat() if self.merged_date else None
        }
    
    def is_active(self) -> bool:
        """
        Verificar si el pull request está activo
        
        Returns:
            bool: True si está activo, False en caso contrario
        """
        return self.state == PullRequestState.OPEN
    
    def get_age_days(self) -> int:
        """
        Obtener edad del pull request en días
        
        Returns:
            int: Edad en días
        """
        if self.closed_date:
            return (self.closed_date - self.created_date).days
        else:
            return (datetime.now() - self.created_date).days
