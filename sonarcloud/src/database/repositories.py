"""
Repositorios de base de datos para SonarCloud

Proporciona clases para operaciones CRUD en la base de datos
para organizaciones, proyectos, quality gates, métricas, issues
y security hotspots.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from ..models import (
    Organization, Project, QualityGate, Metric, Issue, SecurityHotspot
)
from ..utils.logger import get_logger


class BaseRepository:
    """
    Repositorio base con operaciones comunes
    
    Proporciona métodos básicos de CRUD que pueden ser heredados
    por repositorios específicos.
    """
    
    def __init__(self, model_class):
        """
        Inicializar repositorio base
        
        Args:
            model_class: Clase del modelo SQLAlchemy
        """
        self.model_class = model_class
        self.logger = get_logger(f"{__name__}.{model_class.__name__}")
    
    def create(self, session: Session, **kwargs) -> Any:
        """
        Crear nueva instancia
        
        Args:
            session: Sesión de SQLAlchemy
            **kwargs: Atributos del modelo
            
        Returns:
            Instancia creada
        """
        try:
            instance = self.model_class(**kwargs)
            session.add(instance)
            session.flush()  # Para obtener el ID
            self.logger.debug(f"Instancia creada - ID: {instance.id}")
            return instance
        except Exception as e:
            self.logger.error(f"Error al crear instancia: {str(e)}")
            raise
    
    def get_by_id(self, session: Session, id: int) -> Optional[Any]:
        """
        Obtener instancia por ID
        
        Args:
            session: Sesión de SQLAlchemy
            id: ID de la instancia
            
        Returns:
            Instancia encontrada o None
        """
        try:
            instance = session.query(self.model_class).filter(
                self.model_class.id == id
            ).first()
            return instance
        except Exception as e:
            self.logger.error(f"Error al obtener por ID {id}: {str(e)}")
            raise
    
    def get_all(self, session: Session, limit: Optional[int] = None) -> List[Any]:
        """
        Obtener todas las instancias
        
        Args:
            session: Sesión de SQLAlchemy
            limit: Límite de resultados
            
        Returns:
            Lista de instancias
        """
        try:
            query = session.query(self.model_class)
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error al obtener todas las instancias: {str(e)}")
            raise
    
    def update(self, session: Session, id: int, **kwargs) -> Optional[Any]:
        """
        Actualizar instancia
        
        Args:
            session: Sesión de SQLAlchemy
            id: ID de la instancia
            **kwargs: Atributos a actualizar
            
        Returns:
            Instancia actualizada o None
        """
        try:
            instance = self.get_by_id(session, id)
            if instance:
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                session.flush()
                self.logger.debug(f"Instancia actualizada - ID: {id}")
            return instance
        except Exception as e:
            self.logger.error(f"Error al actualizar instancia {id}: {str(e)}")
            raise
    
    def delete(self, session: Session, id: int) -> bool:
        """
        Eliminar instancia
        
        Args:
            session: Sesión de SQLAlchemy
            id: ID de la instancia
            
        Returns:
            True si se eliminó, False en caso contrario
        """
        try:
            instance = self.get_by_id(session, id)
            if instance:
                session.delete(instance)
                session.flush()
                self.logger.debug(f"Instancia eliminada - ID: {id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error al eliminar instancia {id}: {str(e)}")
            raise
    
    def count(self, session: Session) -> int:
        """
        Contar total de instancias
        
        Args:
            session: Sesión de SQLAlchemy
            
        Returns:
            Número total de instancias
        """
        try:
            return session.query(self.model_class).count()
        except Exception as e:
            self.logger.error(f"Error al contar instancias: {str(e)}")
            raise


class OrganizationRepository(BaseRepository):
    """Repositorio para organizaciones de SonarCloud"""
    
    def __init__(self):
        super().__init__(Organization)
    
    def get_by_key(self, session: Session, key: str) -> Optional[Organization]:
        """
        Obtener organización por clave
        
        Args:
            session: Sesión de SQLAlchemy
            key: Clave de la organización
            
        Returns:
            Organización encontrada o None
        """
        try:
            return session.query(Organization).filter(
                Organization.key == key
            ).first()
        except Exception as e:
            self.logger.error(f"Error al obtener organización por clave {key}: {str(e)}")
            raise
    
    def get_by_sonarcloud_id(self, session: Session, sonarcloud_id: str) -> Optional[Organization]:
        """
        Obtener organización por ID de SonarCloud
        
        Args:
            session: Sesión de SQLAlchemy
            sonarcloud_id: ID de SonarCloud
            
        Returns:
            Organización encontrada o None
        """
        try:
            return session.query(Organization).filter(
                Organization.sonarcloud_id == sonarcloud_id
            ).first()
        except Exception as e:
            self.logger.error(f"Error al obtener organización por SonarCloud ID {sonarcloud_id}: {str(e)}")
            raise
    
    def get_default_organization(self, session: Session) -> Optional[Organization]:
        """
        Obtener organización por defecto
        
        Args:
            session: Sesión de SQLAlchemy
            
        Returns:
            Organización por defecto o None
        """
        try:
            return session.query(Organization).filter(
                Organization.is_default == True
            ).first()
        except Exception as e:
            self.logger.error(f"Error al obtener organización por defecto: {str(e)}")
            raise


class ProjectRepository(BaseRepository):
    """Repositorio para proyectos de SonarCloud"""
    
    def __init__(self):
        super().__init__(Project)
    
    def get_by_key(self, session: Session, key: str) -> Optional[Project]:
        """
        Obtener proyecto por clave
        
        Args:
            session: Sesión de SQLAlchemy
            key: Clave del proyecto
            
        Returns:
            Proyecto encontrado o None
        """
        try:
            return session.query(Project).filter(
                Project.key == key
            ).first()
        except Exception as e:
            self.logger.error(f"Error al obtener proyecto por clave {key}: {str(e)}")
            raise
    
    def get_by_sonarcloud_id(self, session: Session, sonarcloud_id: str) -> Optional[Project]:
        """
        Obtener proyecto por ID de SonarCloud
        
        Args:
            session: Sesión de SQLAlchemy
            sonarcloud_id: ID de SonarCloud
            
        Returns:
            Proyecto encontrado o None
        """
        try:
            return session.query(Project).filter(
                Project.sonarcloud_id == sonarcloud_id
            ).first()
        except Exception as e:
            self.logger.error(f"Error al obtener proyecto por SonarCloud ID {sonarcloud_id}: {str(e)}")
            raise
    
    def get_by_organization(self, session: Session, organization_id: int) -> List[Project]:
        """
        Obtener proyectos por organización
        
        Args:
            session: Sesión de SQLAlchemy
            organization_id: ID de la organización
            
        Returns:
            Lista de proyectos
        """
        try:
            return session.query(Project).filter(
                Project.organization_id == organization_id
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener proyectos por organización {organization_id}: {str(e)}")
            raise
    
    def get_by_organization_key(self, session: Session, organization_key: str) -> List[Project]:
        """
        Obtener proyectos por clave de organización
        
        Args:
            session: Sesión de SQLAlchemy
            organization_key: Clave de la organización
            
        Returns:
            Lista de proyectos
        """
        try:
            return session.query(Project).filter(
                Project.organization_key == organization_key
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener proyectos por organización key {organization_key}: {str(e)}")
            raise
    
    def get_projects_by_quality_score(
        self,
        session: Session,
        min_score: float = 0.0,
        max_score: float = 100.0,
        limit: Optional[int] = None
    ) -> List[Project]:
        """
        Obtener proyectos ordenados por score de calidad
        
        Args:
            session: Sesión de SQLAlchemy
            min_score: Score mínimo
            max_score: Score máximo
            limit: Límite de resultados
            
        Returns:
            Lista de proyectos ordenados
        """
        try:
            # Calcular score de calidad para cada proyecto
            projects = session.query(Project).all()
            
            # Calcular scores y filtrar
            scored_projects = []
            for project in projects:
                score = project.get_quality_score()
                if min_score <= score <= max_score:
                    scored_projects.append((project, score))
            
            # Ordenar por score descendente
            scored_projects.sort(key=lambda x: x[1], reverse=True)
            
            # Aplicar límite
            if limit:
                scored_projects = scored_projects[:limit]
            
            return [project for project, score in scored_projects]
            
        except Exception as e:
            self.logger.error(f"Error al obtener proyectos por quality score: {str(e)}")
            raise
    
    def get_projects_by_coverage(
        self,
        session: Session,
        min_coverage: float = 0.0,
        max_coverage: float = 100.0,
        limit: Optional[int] = None
    ) -> List[Project]:
        """
        Obtener proyectos por rango de cobertura
        
        Args:
            session: Sesión de SQLAlchemy
            min_coverage: Cobertura mínima
            max_coverage: Cobertura máxima
            limit: Límite de resultados
            
        Returns:
            Lista de proyectos
        """
        try:
            query = session.query(Project).filter(
                and_(
                    Project.coverage >= min_coverage,
                    Project.coverage <= max_coverage
                )
            ).order_by(desc(Project.coverage))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except Exception as e:
            self.logger.error(f"Error al obtener proyectos por cobertura: {str(e)}")
            raise
    
    def get_projects_by_quality_gate_status(
        self,
        session: Session,
        status: str
    ) -> List[Project]:
        """
        Obtener proyectos por estado de quality gate
        
        Args:
            session: Sesión de SQLAlchemy
            status: Estado del quality gate
            
        Returns:
            Lista de proyectos
        """
        try:
            return session.query(Project).filter(
                Project.quality_gate_status == status
            ).all()
            
        except Exception as e:
            self.logger.error(f"Error al obtener proyectos por quality gate status {status}: {str(e)}")
            raise
    
    def get_projects_with_issues(
        self,
        session: Session,
        min_issues: int = 1,
        limit: Optional[int] = None
    ) -> List[Project]:
        """
        Obtener proyectos con issues
        
        Args:
            session: Sesión de SQLAlchemy
            min_issues: Número mínimo de issues
            limit: Límite de resultados
            
        Returns:
            Lista de proyectos
        """
        try:
            query = session.query(Project).filter(
                or_(
                    Project.bugs_count >= min_issues,
                    Project.vulnerabilities_count >= min_issues,
                    Project.code_smells_count >= min_issues
                )
            ).order_by(
                desc(Project.bugs_count + Project.vulnerabilities_count + Project.code_smells_count)
            )
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except Exception as e:
            self.logger.error(f"Error al obtener proyectos con issues: {str(e)}")
            raise


class QualityGateRepository(BaseRepository):
    """Repositorio para quality gates de SonarCloud"""
    
    def __init__(self):
        super().__init__(QualityGate)
    
    def get_by_project(self, session: Session, project_id: int) -> List[QualityGate]:
        """
        Obtener quality gates por proyecto
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            
        Returns:
            Lista de quality gates
        """
        try:
            return session.query(QualityGate).filter(
                QualityGate.project_id == project_id
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener quality gates por proyecto {project_id}: {str(e)}")
            raise
    
    def get_by_status(self, session: Session, status: str) -> List[QualityGate]:
        """
        Obtener quality gates por estado
        
        Args:
            session: Sesión de SQLAlchemy
            status: Estado del quality gate
            
        Returns:
            Lista de quality gates
        """
        try:
            return session.query(QualityGate).filter(
                QualityGate.status == status
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener quality gates por estado {status}: {str(e)}")
            raise
    
    def get_failed_quality_gates(self, session: Session) -> List[QualityGate]:
        """
        Obtener quality gates fallidos
        
        Args:
            session: Sesión de SQLAlchemy
            
        Returns:
            Lista de quality gates fallidos
        """
        try:
            return session.query(QualityGate).filter(
                QualityGate.status == 'FAILED'
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener quality gates fallidos: {str(e)}")
            raise


class MetricRepository(BaseRepository):
    """Repositorio para métricas de SonarCloud"""
    
    def __init__(self):
        super().__init__(Metric)
    
    def get_by_project(self, session: Session, project_id: int) -> List[Metric]:
        """
        Obtener métricas por proyecto
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            
        Returns:
            Lista de métricas
        """
        try:
            return session.query(Metric).filter(
                Metric.project_id == project_id
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener métricas por proyecto {project_id}: {str(e)}")
            raise
    
    def get_by_key(self, session: Session, project_id: int, key: str) -> Optional[Metric]:
        """
        Obtener métrica por clave y proyecto
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            key: Clave de la métrica
            
        Returns:
            Métrica encontrada o None
        """
        try:
            return session.query(Metric).filter(
                and_(
                    Metric.project_id == project_id,
                    Metric.key == key
                )
            ).first()
        except Exception as e:
            self.logger.error(f"Error al obtener métrica por clave {key} y proyecto {project_id}: {str(e)}")
            raise
    
    def get_by_domain(self, session: Session, project_id: int, domain: str) -> List[Metric]:
        """
        Obtener métricas por dominio
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            domain: Dominio de las métricas
            
        Returns:
            Lista de métricas
        """
        try:
            return session.query(Metric).filter(
                and_(
                    Metric.project_id == project_id,
                    Metric.domain == domain
                )
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener métricas por dominio {domain} y proyecto {project_id}: {str(e)}")
            raise


class IssueRepository(BaseRepository):
    """Repositorio para issues de SonarCloud"""
    
    def __init__(self):
        super().__init__(Issue)
    
    def get_by_project(self, session: Session, project_id: int) -> List[Issue]:
        """
        Obtener issues por proyecto
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            
        Returns:
            Lista de issues
        """
        try:
            return session.query(Issue).filter(
                Issue.project_id == project_id
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener issues por proyecto {project_id}: {str(e)}")
            raise
    
    def get_by_severity(self, session: Session, project_id: int, severity: str) -> List[Issue]:
        """
        Obtener issues por severidad
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            severity: Severidad de los issues
            
        Returns:
            Lista de issues
        """
        try:
            return session.query(Issue).filter(
                and_(
                    Issue.project_id == project_id,
                    Issue.severity == severity
                )
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener issues por severidad {severity} y proyecto {project_id}: {str(e)}")
            raise
    
    def get_by_type(self, session: Session, project_id: int, issue_type: str) -> List[Issue]:
        """
        Obtener issues por tipo
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            issue_type: Tipo de issue
            
        Returns:
            Lista de issues
        """
        try:
            return session.query(Issue).filter(
                and_(
                    Issue.project_id == project_id,
                    Issue.type == issue_type
                )
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener issues por tipo {issue_type} y proyecto {project_id}: {str(e)}")
            raise
    
    def get_open_issues(self, session: Session, project_id: int) -> List[Issue]:
        """
        Obtener issues abiertos
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            
        Returns:
            Lista de issues abiertos
        """
        try:
            return session.query(Issue).filter(
                and_(
                    Issue.project_id == project_id,
                    Issue.status.in_(['OPEN', 'CONFIRMED', 'REOPENED'])
                )
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener issues abiertos por proyecto {project_id}: {str(e)}")
            raise
    
    def get_issues_by_assignee(self, session: Session, project_id: int, assignee: str) -> List[Issue]:
        """
        Obtener issues por asignado
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            assignee: Usuario asignado
            
        Returns:
            Lista de issues
        """
        try:
            return session.query(Issue).filter(
                and_(
                    Issue.project_id == project_id,
                    Issue.assignee == assignee
                )
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener issues por asignado {assignee} y proyecto {project_id}: {str(e)}")
            raise


class SecurityHotspotRepository(BaseRepository):
    """Repositorio para security hotspots de SonarCloud"""
    
    def __init__(self):
        super().__init__(SecurityHotspot)
    
    def get_by_project(self, session: Session, project_id: int) -> List[SecurityHotspot]:
        """
        Obtener security hotspots por proyecto
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            
        Returns:
            Lista de security hotspots
        """
        try:
            return session.query(SecurityHotspot).filter(
                SecurityHotspot.project_id == project_id
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener security hotspots por proyecto {project_id}: {str(e)}")
            raise
    
    def get_by_vulnerability_probability(
        self,
        session: Session,
        project_id: int,
        probability: str
    ) -> List[SecurityHotspot]:
        """
        Obtener security hotspots por probabilidad de vulnerabilidad
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            probability: Probabilidad de vulnerabilidad
            
        Returns:
            Lista de security hotspots
        """
        try:
            return session.query(SecurityHotspot).filter(
                and_(
                    SecurityHotspot.project_id == project_id,
                    SecurityHotspot.vulnerability_probability == probability
                )
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener security hotspots por probabilidad {probability} y proyecto {project_id}: {str(e)}")
            raise
    
    def get_by_status(self, session: Session, project_id: int, status: str) -> List[SecurityHotspot]:
        """
        Obtener security hotspots por estado
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            status: Estado del security hotspot
            
        Returns:
            Lista de security hotspots
        """
        try:
            return session.query(SecurityHotspot).filter(
                and_(
                    SecurityHotspot.project_id == project_id,
                    SecurityHotspot.status == status
                )
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener security hotspots por estado {status} y proyecto {project_id}: {str(e)}")
            raise
    
    def get_to_review_hotspots(self, session: Session, project_id: int) -> List[SecurityHotspot]:
        """
        Obtener security hotspots pendientes de revisión
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            
        Returns:
            Lista de security hotspots pendientes de revisión
        """
        try:
            return session.query(SecurityHotspot).filter(
                and_(
                    SecurityHotspot.project_id == project_id,
                    SecurityHotspot.status == 'TO_REVIEW'
                )
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener security hotspots pendientes de revisión por proyecto {project_id}: {str(e)}")
            raise
    
    def get_high_risk_hotspots(self, session: Session, project_id: int) -> List[SecurityHotspot]:
        """
        Obtener security hotspots de alto riesgo
        
        Args:
            session: Sesión de SQLAlchemy
            project_id: ID del proyecto
            
        Returns:
            Lista de security hotspots de alto riesgo
        """
        try:
            return session.query(SecurityHotspot).filter(
                and_(
                    SecurityHotspot.project_id == project_id,
                    SecurityHotspot.vulnerability_probability == 'HIGH'
                )
            ).all()
        except Exception as e:
            self.logger.error(f"Error al obtener security hotspots de alto riesgo por proyecto {project_id}: {str(e)}")
            raise
