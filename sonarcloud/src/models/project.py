"""
Modelo para proyectos de SonarCloud
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Project(Base):
    """
    Modelo para proyectos de SonarCloud
    
    Representa un proyecto en SonarCloud con sus métricas de calidad
    y propiedades asociadas.
    """
    
    __tablename__ = 'projects'
    
    # Campos de identificación
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Campos de SonarCloud
    sonarcloud_id = Column(String(255), unique=True, nullable=False, index=True)
    organization_key = Column(String(255), nullable=False, index=True)
    visibility = Column(String(50), nullable=False, default='private')
    
    # Campos de configuración
    is_private = Column(Boolean, default=True, nullable=False)
    language = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)  # JSON string de tags
    
    # Campos de fechas
    last_analysis_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Métricas de calidad de código
    coverage = Column(Float, default=0.0, nullable=False)  # Porcentaje de cobertura
    duplications = Column(Float, default=0.0, nullable=False)  # Porcentaje de duplicación
    maintainability_rating = Column(Integer, default=1, nullable=False)  # A-E rating
    reliability_rating = Column(Integer, default=1, nullable=False)  # A-E rating
    security_rating = Column(Integer, default=1, nullable=False)  # A-E rating
    security_review_rating = Column(Integer, default=1, nullable=False)  # A-E rating
    
    # Métricas de issues
    bugs_count = Column(Integer, default=0, nullable=False)
    vulnerabilities_count = Column(Integer, default=0, nullable=False)
    code_smells_count = Column(Integer, default=0, nullable=False)
    new_issues_count = Column(Integer, default=0, nullable=False)
    
    # Métricas de security hotspots
    security_hotspots_count = Column(Integer, default=0, nullable=False)
    security_hotspots_reviewed_count = Column(Integer, default=0, nullable=False)
    
    # Métricas de líneas de código
    lines_of_code = Column(Integer, default=0, nullable=False)
    ncloc = Column(Integer, default=0, nullable=False)  # Non-commenting lines of code
    
    # Quality Gate
    alert_status = Column(String(50), nullable=True)  # OK, WARN, ERROR
    quality_gate_status = Column(String(50), nullable=True)  # PASSED, FAILED
    
    # Relaciones
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    organization = relationship("Organization", back_populates="projects")
    quality_gates = relationship("QualityGate", back_populates="project", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="project", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")
    security_hotspots = relationship("SecurityHotspot", back_populates="project", cascade="all, delete-orphan")
    
    @classmethod
    def from_sonarcloud_data(cls, data: dict, organization_id: int) -> 'Project':
        """
        Crear instancia desde datos de la API de SonarCloud
        
        Args:
            data: Datos del proyecto desde SonarCloud
            organization_id: ID de la organización
            
        Returns:
            Project: Instancia del proyecto
        """
        import uuid as uuid_lib
        import json
        
        # Parsear fecha de último análisis
        last_analysis_date = None
        if data.get('lastAnalysisDate'):
            try:
                last_analysis_date = datetime.fromisoformat(data['lastAnalysisDate'].replace('Z', '+00:00'))
            except:
                pass
        
        # Parsear tags
        tags = None
        if data.get('tags'):
            tags = json.dumps(data['tags'])
        
        return cls(
            uuid=str(uuid_lib.uuid4()),
            key=data.get('key'),
            name=data.get('name'),
            description=data.get('description'),
            sonarcloud_id=data.get('id'),
            organization_key=data.get('organization'),
            visibility=data.get('visibility', 'private'),
            is_private=data.get('private', True),
            language=data.get('language'),
            tags=tags,
            last_analysis_date=last_analysis_date,
            organization_id=organization_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def update_from_sonarcloud_data(self, data: dict) -> None:
        """
        Actualizar proyecto desde datos de la API de SonarCloud
        
        Args:
            data: Datos del proyecto desde SonarCloud
        """
        import json
        
        self.name = data.get('name', self.name)
        self.description = data.get('description', self.description)
        self.visibility = data.get('visibility', self.visibility)
        self.is_private = data.get('private', self.is_private)
        self.language = data.get('language', self.language)
        
        # Parsear tags
        if data.get('tags'):
            self.tags = json.dumps(data['tags'])
        
        # Parsear fecha de último análisis
        if data.get('lastAnalysisDate'):
            try:
                self.last_analysis_date = datetime.fromisoformat(data['lastAnalysisDate'].replace('Z', '+00:00'))
            except:
                pass
        
        self.updated_at = datetime.now()
    
    def update_quality_metrics(self, metrics_data: dict) -> None:
        """
        Actualizar métricas de calidad del proyecto
        
        Args:
            metrics_data: Datos de métricas desde SonarCloud
        """
        # Métricas de cobertura y duplicación
        self.coverage = float(metrics_data.get('coverage', 0))
        self.duplications = float(metrics_data.get('duplicated_lines_density', 0))
        
        # Ratings de calidad
        self.maintainability_rating = self._parse_rating(metrics_data.get('sqale_rating', 'A'))
        self.reliability_rating = self._parse_rating(metrics_data.get('reliability_rating', 'A'))
        self.security_rating = self._parse_rating(metrics_data.get('security_rating', 'A'))
        self.security_review_rating = self._parse_rating(metrics_data.get('security_review_rating', 'A'))
        
        # Métricas de issues
        self.bugs_count = int(metrics_data.get('bugs', 0))
        self.vulnerabilities_count = int(metrics_data.get('vulnerabilities', 0))
        self.code_smells_count = int(metrics_data.get('code_smells', 0))
        self.new_issues_count = int(metrics_data.get('new_issues', 0))
        
        # Métricas de security hotspots
        self.security_hotspots_count = int(metrics_data.get('security_hotspots', 0))
        self.security_hotspots_reviewed_count = int(metrics_data.get('security_hotspots_reviewed', 0))
        
        # Métricas de líneas de código
        self.lines_of_code = int(metrics_data.get('lines', 0))
        self.ncloc = int(metrics_data.get('ncloc', 0))
        
        # Quality Gate
        self.alert_status = metrics_data.get('alert_status')
        self.quality_gate_status = metrics_data.get('quality_gate_status')
        
        self.updated_at = datetime.now()
    
    def _parse_rating(self, rating: str) -> int:
        """
        Convertir rating de letra a número
        
        Args:
            rating: Rating en formato letra (A-E)
            
        Returns:
            int: Rating en formato número (1-5)
        """
        rating_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
        return rating_map.get(rating.upper(), 1)
    
    def get_quality_score(self) -> float:
        """
        Calcular score de calidad general del proyecto
        
        Returns:
            float: Score de calidad (0-100)
        """
        # Cálculo basado en múltiples factores
        score = 0.0
        
        # Cobertura (30% del score)
        score += ((self.coverage or 0) / 100.0) * 30
        
        # Duplicación (20% del score) - menor es mejor
        duplication_score = max(0, 100 - (self.duplications or 0))
        score += (duplication_score / 100.0) * 20
        
        # Ratings de calidad (30% del score)
        ratings_score = 0
        ratings_score += (6 - (self.maintainability_rating or 5)) * 6  # A=5, B=4, etc.
        ratings_score += (6 - (self.reliability_rating or 5)) * 6
        ratings_score += (6 - (self.security_rating or 5)) * 6
        ratings_score += (6 - (self.security_review_rating or 5)) * 6
        score += (ratings_score / 120.0) * 30  # Máximo 120 puntos
        
        # Issues (20% del score) - menos issues es mejor
        total_issues = (self.bugs_count or 0) + (self.vulnerabilities_count or 0) + (self.code_smells_count or 0)
        if total_issues == 0:
            score += 20
        else:
            issues_score = max(0, 100 - (total_issues * 2))  # Penalizar por issues
            score += (issues_score / 100.0) * 20
        
        return min(100.0, max(0.0, score))
    
    def get_quality_summary(self) -> dict:
        """
        Obtener resumen de calidad del proyecto
        
        Returns:
            dict: Resumen de calidad
        """
        return {
            'quality_score': self.get_quality_score(),
            'coverage': self.coverage,
            'duplications': self.duplications,
            'maintainability_rating': self._rating_to_letter(self.maintainability_rating),
            'reliability_rating': self._rating_to_letter(self.reliability_rating),
            'security_rating': self._rating_to_letter(self.security_rating),
            'security_review_rating': self._rating_to_letter(self.security_review_rating),
            'total_issues': self.bugs_count + self.vulnerabilities_count + self.code_smells_count,
            'new_issues': self.new_issues_count,
            'security_hotspots': self.security_hotspots_count,
            'quality_gate_status': self.quality_gate_status,
            'alert_status': self.alert_status
        }
    
    def _rating_to_letter(self, rating: int) -> str:
        """
        Convertir rating de número a letra
        
        Args:
            rating: Rating en formato número (1-5)
            
        Returns:
            str: Rating en formato letra (A-E)
        """
        rating_map = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E'}
        return rating_map.get(rating, 'A')
    
    def __repr__(self) -> str:
        return f"<Project(key='{self.key}', name='{self.name}')>"
