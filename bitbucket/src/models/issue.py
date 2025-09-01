"""
Modelo para Issue de SonarCloud
"""

from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base


class IssueSeverity(enum.Enum):
    """Enumeración para severidad de issues"""
    BLOCKER = "BLOCKER"
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFO = "INFO"


class IssueType(enum.Enum):
    """Enumeración para tipo de issues"""
    BUG = "BUG"
    VULNERABILITY = "VULNERABILITY"
    CODE_SMELL = "CODE_SMELL"


class IssueStatus(enum.Enum):
    """Enumeración para estado de issues"""
    OPEN = "OPEN"
    CONFIRMED = "CONFIRMED"
    REOPENED = "REOPENED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Issue(Base):
    """
    Modelo para representar un Issue de SonarCloud
    
    Un issue representa un problema de calidad de código
    """
    
    __tablename__ = 'issues'
    
    # Campos de identificación
    sonarcloud_id = Column(String(100), unique=True, nullable=False, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    
    # Campos de información
    rule = Column(String(100), nullable=False)  # Regla que generó el issue
    severity = Column(Enum(IssueSeverity), nullable=False)
    type = Column(Enum(IssueType), nullable=False)
    status = Column(Enum(IssueStatus), nullable=False)
    
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
    close_date = Column(DateTime(), nullable=True)
    
    # Campos de autor
    author = Column(String(200), nullable=True)
    assignee = Column(String(200), nullable=True)
    
    # Relación con SonarCloudProject
    sonarcloud_project_id = Column(Integer, ForeignKey('sonarcloud_projects.id'), nullable=False)
    sonarcloud_project = relationship("SonarCloudProject", back_populates="issues")
    
    def __repr__(self) -> str:
        """Representación string del issue"""
        return f"<Issue(key='{self.key}', rule='{self.rule}', severity='{self.severity.value}')>"
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict, sonarcloud_project_id: int) -> 'Issue':
        """
        Crear instancia de Issue desde datos de la API de SonarCloud
        
        Args:
            data: Datos del issue desde la API
            sonarcloud_project_id: ID del proyecto de SonarCloud
            
        Returns:
            Issue: Nueva instancia del issue
        """
        return cls(
            sonarcloud_id=data.get('id'),
            key=data.get('key'),
            rule=data.get('rule'),
            severity=IssueSeverity(data.get('severity', 'INFO')),
            type=IssueType(data.get('type', 'CODE_SMELL')),
            status=IssueStatus(data.get('status', 'OPEN')),
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
            close_date=data.get('closeDate'),
            author=data.get('author'),
            assignee=data.get('assignee'),
            sonarcloud_project_id=sonarcloud_project_id
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar issue desde datos de la API de SonarCloud
        
        Args:
            data: Datos del issue desde la API
        """
        self.rule = data.get('rule', self.rule)
        self.severity = IssueSeverity(data.get('severity', self.severity.value))
        self.type = IssueType(data.get('type', self.type.value))
        self.status = IssueStatus(data.get('status', self.status.value))
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
        self.close_date = data.get('closeDate', self.close_date)
        self.author = data.get('author', self.author)
        self.assignee = data.get('assignee', self.assignee)
