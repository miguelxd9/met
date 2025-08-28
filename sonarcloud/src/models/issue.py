"""
Modelo para issues de SonarCloud
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Issue(Base):
    """
    Modelo para issues de SonarCloud
    
    Representa un issue de calidad de código encontrado en un proyecto
    con su información detallada y estado.
    """
    
    __tablename__ = 'issues'
    
    # Campos de identificación
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    
    # Campos de SonarCloud
    sonarcloud_id = Column(String(255), unique=True, nullable=False, index=True)
    project_key = Column(String(255), nullable=False, index=True)
    
    # Campos de información del issue
    rule = Column(String(255), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)  # BLOCKER, CRITICAL, MAJOR, MINOR, INFO
    type = Column(String(50), nullable=False, index=True)  # BUG, VULNERABILITY, CODE_SMELL
    status = Column(String(50), nullable=False, index=True)  # OPEN, CONFIRMED, REOPENED, RESOLVED, CLOSED
    resolution = Column(String(50), nullable=True)  # FIXED, WONTFIX, FALSEPOSITIVE, REMOVED
    
    # Campos de ubicación
    component = Column(String(500), nullable=True)
    line = Column(Integer, nullable=True)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    
    # Campos de información
    message = Column(Text, nullable=True)
    effort = Column(String(100), nullable=True)
    debt = Column(String(100), nullable=True)
    
    # Campos de autor y asignación
    author = Column(String(255), nullable=True)
    assignee = Column(String(255), nullable=True)
    
    # Campos de fechas
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Campos de metadatos
    tags = Column(Text, nullable=True)  # JSON string de tags
    transitions = Column(Text, nullable=True)  # JSON string de transiciones
    
    # Relaciones
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    project = relationship("Project", back_populates="issues")
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict, project_id: int) -> 'Issue':
        """
        Crear instancia desde datos de la API de SonarCloud
        
        Args:
            data: Datos del issue desde SonarCloud
            project_id: ID del proyecto
            
        Returns:
            Issue: Instancia del issue
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
        
        closed_at = None
        if data.get('closeDate'):
            try:
                closed_at = datetime.fromisoformat(data['closeDate'].replace('Z', '+00:00'))
            except:
                pass
        
        # Parsear JSON fields
        tags = None
        if data.get('tags'):
            tags = json.dumps(data['tags'])
        
        transitions = None
        if data.get('transitions'):
            transitions = json.dumps(data['transitions'])
        
        return cls(
            uuid=str(uuid_lib.uuid4()),
            key=data.get('key'),
            sonarcloud_id=data.get('id'),
            project_key=data.get('project'),
            rule=data.get('rule'),
            severity=data.get('severity'),
            type=data.get('type'),
            status=data.get('status'),
            resolution=data.get('resolution'),
            component=data.get('component'),
            line=data.get('line'),
            start_line=data.get('startLine'),
            end_line=data.get('endLine'),
            start_offset=data.get('startOffset'),
            end_offset=data.get('endOffset'),
            message=data.get('message'),
            effort=data.get('effort'),
            debt=data.get('debt'),
            author=data.get('author'),
            assignee=data.get('assignee'),
            created_at=created_at,
            updated_at=updated_at,
            closed_at=closed_at,
            tags=tags,
            transitions=transitions,
            project_id=project_id
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar issue desde datos de la API de SonarCloud
        
        Args:
            data: Datos del issue desde SonarCloud
        """
        import json
        
        self.rule = data.get('rule', self.rule)
        self.severity = data.get('severity', self.severity)
        self.type = data.get('type', self.type)
        self.status = data.get('status', self.status)
        self.resolution = data.get('resolution', self.resolution)
        self.component = data.get('component', self.component)
        self.line = data.get('line', self.line)
        self.start_line = data.get('startLine', self.start_line)
        self.end_line = data.get('endLine', self.end_line)
        self.start_offset = data.get('startOffset', self.start_offset)
        self.end_offset = data.get('endOffset', self.end_offset)
        self.message = data.get('message', self.message)
        self.effort = data.get('effort', self.effort)
        self.debt = data.get('debt', self.debt)
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
        
        if data.get('closeDate'):
            try:
                self.closed_at = datetime.fromisoformat(data['closeDate'].replace('Z', '+00:00'))
            except:
                pass
        
        # Parsear JSON fields
        if data.get('tags'):
            self.tags = json.dumps(data['tags'])
        
        if data.get('transitions'):
            self.transitions = json.dumps(data['transitions'])
    
    def is_open(self) -> bool:
        """
        Verificar si el issue está abierto
        
        Returns:
            bool: True si está abierto, False en caso contrario
        """
        return self.status in ['OPEN', 'CONFIRMED', 'REOPENED']
    
    def is_resolved(self) -> bool:
        """
        Verificar si el issue está resuelto
        
        Returns:
            bool: True si está resuelto, False en caso contrario
        """
        return self.status in ['RESOLVED', 'CLOSED']
    
    def is_closed(self) -> bool:
        """
        Verificar si el issue está cerrado
        
        Returns:
            bool: True si está cerrado, False en caso contrario
        """
        return self.status == 'CLOSED'
    
    def get_severity_weight(self) -> int:
        """
        Obtener peso de severidad para ordenamiento
        
        Returns:
            int: Peso de severidad (mayor = más severo)
        """
        severity_weights = {
            'BLOCKER': 5,
            'CRITICAL': 4,
            'MAJOR': 3,
            'MINOR': 2,
            'INFO': 1
        }
        return severity_weights.get(self.severity, 0)
    
    def get_type_weight(self) -> int:
        """
        Obtener peso de tipo para ordenamiento
        
        Returns:
            int: Peso de tipo (mayor = más importante)
        """
        type_weights = {
            'BUG': 3,
            'VULNERABILITY': 3,
            'CODE_SMELL': 1
        }
        return type_weights.get(self.type, 0)
    
    def get_summary(self) -> dict:
        """
        Obtener resumen del issue
        
        Returns:
            dict: Resumen del issue
        """
        return {
            'key': self.key,
            'rule': self.rule,
            'severity': self.severity,
            'type': self.type,
            'status': self.status,
            'resolution': self.resolution,
            'message': self.message,
            'component': self.component,
            'line': self.line,
            'author': self.author,
            'assignee': self.assignee,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_open': self.is_open(),
            'is_resolved': self.is_resolved(),
            'is_closed': self.is_closed()
        }
    
    def __repr__(self) -> str:
        return f"<Issue(key='{self.key}', severity='{self.severity}', type='{self.type}')>"
