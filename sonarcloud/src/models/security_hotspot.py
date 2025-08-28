"""
Modelo para Security Hotspots de SonarCloud
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class SecurityHotspot(Base):
    """
    Modelo para Security Hotspots de SonarCloud
    
    Representa un security hotspot encontrado en un proyecto
    con su información detallada y estado de revisión.
    """
    
    __tablename__ = 'security_hotspots'
    
    # Campos de identificación
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    
    # Campos de SonarCloud
    sonarcloud_id = Column(String(255), unique=True, nullable=False, index=True)
    project_key = Column(String(255), nullable=False, index=True)
    
    # Campos de información del hotspot
    rule_key = Column(String(255), nullable=False, index=True)
    vulnerability_probability = Column(String(50), nullable=False, index=True)  # HIGH, MEDIUM, LOW
    security_category = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, index=True)  # TO_REVIEW, REVIEWED, SAFE, FIXED
    
    # Campos de ubicación
    component = Column(String(500), nullable=True)
    line = Column(Integer, nullable=True)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    
    # Campos de información
    message = Column(Text, nullable=True)
    flows = Column(Text, nullable=True)  # JSON string de flows
    
    # Campos de autor y asignación
    author = Column(String(255), nullable=True)
    assignee = Column(String(255), nullable=True)
    
    # Campos de fechas
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Campos de metadatos
    tags = Column(Text, nullable=True)  # JSON string de tags
    
    # Relaciones
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    project = relationship("Project", back_populates="security_hotspots")
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict, project_id: int) -> 'SecurityHotspot':
        """
        Crear instancia desde datos de la API de SonarCloud
        
        Args:
            data: Datos del security hotspot desde SonarCloud
            project_id: ID del proyecto
            
        Returns:
            SecurityHotspot: Instancia del security hotspot
        """
        import uuid as uuid_lib
        import json
        
        # Parsear fechas
        created_at = None
        if data.get('creationDate'):
            try:
                created_at = datetime.fromisoformat(data['creationDate'].replace('Z', '+00:00'))
            except:
                pass
        
        updated_at = None
        if data.get('updateDate'):
            try:
                updated_at = datetime.fromisoformat(data['updateDate'].replace('Z', '+00:00'))
            except:
                pass
        
        resolved_at = None
        if data.get('resolutionDate'):
            try:
                resolved_at = datetime.fromisoformat(data['resolutionDate'].replace('Z', '+00:00'))
            except:
                pass
        
        # Parsear JSON fields
        flows = None
        if data.get('flows'):
            flows = json.dumps(data['flows'])
        
        tags = None
        if data.get('tags'):
            tags = json.dumps(data['tags'])
        
        return cls(
            uuid=str(uuid_lib.uuid4()),
            key=data.get('key'),
            sonarcloud_id=data.get('id'),
            project_key=data.get('project'),
            rule_key=data.get('ruleKey'),
            vulnerability_probability=data.get('vulnerabilityProbability'),
            security_category=data.get('securityCategory'),
            status=data.get('status'),
            component=data.get('component'),
            line=data.get('line'),
            start_line=data.get('startLine'),
            end_line=data.get('endLine'),
            start_offset=data.get('startOffset'),
            end_offset=data.get('endOffset'),
            message=data.get('message'),
            flows=flows,
            author=data.get('author'),
            assignee=data.get('assignee'),
            created_at=created_at,
            updated_at=updated_at,
            resolved_at=resolved_at,
            tags=tags,
            project_id=project_id
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar security hotspot desde datos de la API de SonarCloud
        
        Args:
            data: Datos del security hotspot desde SonarCloud
        """
        import json
        
        self.rule_key = data.get('ruleKey', self.rule_key)
        self.vulnerability_probability = data.get('vulnerabilityProbability', self.vulnerability_probability)
        self.security_category = data.get('securityCategory', self.security_category)
        self.status = data.get('status', self.status)
        self.component = data.get('component', self.component)
        self.line = data.get('line', self.line)
        self.start_line = data.get('startLine', self.start_line)
        self.end_line = data.get('endLine', self.end_line)
        self.start_offset = data.get('startOffset', self.start_offset)
        self.end_offset = data.get('endOffset', self.end_offset)
        self.message = data.get('message', self.message)
        self.author = data.get('author', self.author)
        self.assignee = data.get('assignee', self.assignee)
        
        # Parsear fechas
        if data.get('creationDate'):
            try:
                self.created_at = datetime.fromisoformat(data['creationDate'].replace('Z', '+00:00'))
            except:
                pass
        
        if data.get('updateDate'):
            try:
                self.updated_at = datetime.fromisoformat(data['updateDate'].replace('Z', '+00:00'))
            except:
                pass
        
        if data.get('resolutionDate'):
            try:
                self.resolved_at = datetime.fromisoformat(data['resolutionDate'].replace('Z', '+00:00'))
            except:
                pass
        
        # Parsear JSON fields
        if data.get('flows'):
            self.flows = json.dumps(data['flows'])
        
        if data.get('tags'):
            self.tags = json.dumps(data['tags'])
    
    def is_to_review(self) -> bool:
        """
        Verificar si el hotspot está pendiente de revisión
        
        Returns:
            bool: True si está pendiente de revisión, False en caso contrario
        """
        return self.status == 'TO_REVIEW'
    
    def is_reviewed(self) -> bool:
        """
        Verificar si el hotspot ha sido revisado
        
        Returns:
            bool: True si ha sido revisado, False en caso contrario
        """
        return self.status == 'REVIEWED'
    
    def is_safe(self) -> bool:
        """
        Verificar si el hotspot es seguro
        
        Returns:
            bool: True si es seguro, False en caso contrario
        """
        return self.status == 'SAFE'
    
    def is_fixed(self) -> bool:
        """
        Verificar si el hotspot ha sido corregido
        
        Returns:
            bool: True si ha sido corregido, False en caso contrario
        """
        return self.status == 'FIXED'
    
    def get_vulnerability_weight(self) -> int:
        """
        Obtener peso de vulnerabilidad para ordenamiento
        
        Returns:
            int: Peso de vulnerabilidad (mayor = más vulnerable)
        """
        vulnerability_weights = {
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1
        }
        return vulnerability_weights.get(self.vulnerability_probability, 0)
    
    def get_status_weight(self) -> int:
        """
        Obtener peso de estado para ordenamiento
        
        Returns:
            int: Peso de estado (mayor = más crítico)
        """
        status_weights = {
            'TO_REVIEW': 4,
            'REVIEWED': 3,
            'SAFE': 1,
            'FIXED': 2
        }
        return status_weights.get(self.status, 0)
    
    def get_summary(self) -> dict:
        """
        Obtener resumen del security hotspot
        
        Returns:
            dict: Resumen del security hotspot
        """
        return {
            'key': self.key,
            'rule_key': self.rule_key,
            'vulnerability_probability': self.vulnerability_probability,
            'security_category': self.security_category,
            'status': self.status,
            'message': self.message,
            'component': self.component,
            'line': self.line,
            'author': self.author,
            'assignee': self.assignee,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_to_review': self.is_to_review(),
            'is_reviewed': self.is_reviewed(),
            'is_safe': self.is_safe(),
            'is_fixed': self.is_fixed()
        }
    
    def __repr__(self) -> str:
        return f"<SecurityHotspot(key='{self.key}', probability='{self.vulnerability_probability}', status='{self.status}')>"
