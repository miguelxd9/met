"""
Repositorios de base de datos para SonarCloud

Implementa el patrón Repository para acceder a los datos de:
- Organizations
- SonarCloudProjects
- Issues
- Security Hotspots
- Quality Gates
- Metrics
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func

from src.models import (
    Organization, SonarCloudProject, Issue, SecurityHotspot, QualityGate, Metric
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OrganizationRepository:
    """Repositorio para entidades Organization"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, organization_id: int) -> Optional[Organization]:
        """Obtener organización por ID"""
        return self.session.query(Organization).filter(Organization.id == organization_id).first()
    
    def get_by_key(self, key: str) -> Optional[Organization]:
        """Obtener organización por clave"""
        return self.session.query(Organization).filter(Organization.key == key).first()
    
    def get_by_sonarcloud_id(self, sonarcloud_id: str) -> Optional[Organization]:
        """Obtener organización por ID de SonarCloud"""
        return self.session.query(Organization).filter(Organization.sonarcloud_id == sonarcloud_id).first()
    
    def get_all(self) -> List[Organization]:
        """Obtener todas las organizaciones"""
        return self.session.query(Organization).all()
    
    def create_or_update(self, organization_data: Dict[str, Any]) -> Organization:
        """
        Crear o actualizar organización
        
        Args:
            organization_data: Datos de la organización desde SonarCloud
            
        Returns:
            Organization creada o actualizada
        """
        # Buscar por clave primero
        existing = self.get_by_key(organization_data.get('key'))
        
        if existing:
            # Actualizar existente
            existing.update_from_sonarcloud_data(organization_data)
            self.session.commit()
            logger.debug(f"Organización actualizada - ID: {existing.id}, Key: {existing.key}")
            return existing
        else:
            # Crear nueva
            new_organization = Organization.from_sonarcloud_data(organization_data)
            self.session.add(new_organization)
            self.session.commit()
            logger.info(f"Nueva organización creada - ID: {new_organization.id}, Key: {new_organization.key}, Name: {new_organization.name}")
            return new_organization


class SonarCloudProjectRepository:
    """Repositorio para entidades SonarCloudProject"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, project_id: int) -> Optional[SonarCloudProject]:
        """Obtener proyecto por ID"""
        return self.session.query(SonarCloudProject).filter(SonarCloudProject.id == project_id).first()
    
    def get_by_key(self, key: str) -> Optional[SonarCloudProject]:
        """Obtener proyecto por clave"""
        return self.session.query(SonarCloudProject).filter(SonarCloudProject.key == key).first()
    
    def get_by_sonarcloud_id(self, sonarcloud_id: str) -> Optional[SonarCloudProject]:
        """Obtener proyecto por ID de SonarCloud"""
        return self.session.query(SonarCloudProject).filter(SonarCloudProject.sonarcloud_id == sonarcloud_id).first()
    
    def get_by_organization(self, organization_id: int) -> List[SonarCloudProject]:
        """Obtener proyectos por organización"""
        return self.session.query(SonarCloudProject).filter(SonarCloudProject.organization_id == organization_id).all()
    
    def get_by_scm_url(self, scm_url: str) -> Optional[SonarCloudProject]:
        """Obtener proyecto por URL SCM (para relacionar con Bitbucket)"""
        return self.session.query(SonarCloudProject).filter(SonarCloudProject.scm_url == scm_url).first()
    
    def get_all(self) -> List[SonarCloudProject]:
        """Obtener todos los proyectos"""
        return self.session.query(SonarCloudProject).all()
    
    def create_or_update(
        self,
        project_data: Dict[str, Any],
        organization_id: int
    ) -> SonarCloudProject:
        """
        Crear o actualizar proyecto
        
        Args:
            project_data: Datos del proyecto desde SonarCloud
            organization_id: ID de la organización al que pertenece
            
        Returns:
            SonarCloudProject creado o actualizado
        """
        # Buscar por clave primero
        existing = self.get_by_key(project_data.get('key'))
        
        if existing:
            # Actualizar existente
            existing.update_from_sonarcloud_data(project_data)
            self.session.commit()
            logger.debug(f"Proyecto SonarCloud actualizado - ID: {existing.id}, Key: {existing.key}")
            return existing
        else:
            # Crear nuevo
            new_project = SonarCloudProject.from_sonarcloud_data(project_data, organization_id)
            self.session.add(new_project)
            self.session.commit()
            logger.info(f"Nuevo proyecto SonarCloud creado - ID: {new_project.id}, Key: {new_project.key}, Name: {new_project.name}, Organization ID: {organization_id}")
            return new_project
    
    def link_to_bitbucket_repository(
        self,
        sonarcloud_project_key: str,
        bitbucket_repository_id: int
    ) -> bool:
        """
        Vincular proyecto de SonarCloud con repositorio de Bitbucket
        
        Args:
            sonarcloud_project_key: Clave del proyecto de SonarCloud
            bitbucket_repository_id: ID del repositorio de Bitbucket
            
        Returns:
            True si se vinculó exitosamente, False en caso contrario
        """
        project = self.get_by_key(sonarcloud_project_key)
        if project:
            project.bitbucket_repository_id = bitbucket_repository_id
            self.session.commit()
            logger.info(f"Proyecto SonarCloud vinculado con repositorio Bitbucket - Project: {sonarcloud_project_key}, Repository ID: {bitbucket_repository_id}")
            return True
        return False


class IssueRepository:
    """Repositorio para entidades Issue"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, issue_id: int) -> Optional[Issue]:
        """Obtener issue por ID"""
        return self.session.query(Issue).filter(Issue.id == issue_id).first()
    
    def get_by_key(self, key: str) -> Optional[Issue]:
        """Obtener issue por clave"""
        return self.session.query(Issue).filter(Issue.key == key).first()
    
    def get_by_sonarcloud_id(self, sonarcloud_id: str) -> Optional[Issue]:
        """Obtener issue por ID de SonarCloud"""
        return self.session.query(Issue).filter(Issue.sonarcloud_id == sonarcloud_id).first()
    
    def get_by_project(self, sonarcloud_project_id: int) -> List[Issue]:
        """Obtener issues por proyecto"""
        return self.session.query(Issue).filter(Issue.sonarcloud_project_id == sonarcloud_project_id).all()
    
    def get_by_severity(self, severity: str) -> List[Issue]:
        """Obtener issues por severidad"""
        return self.session.query(Issue).filter(Issue.severity == severity).all()
    
    def get_by_status(self, status: str) -> List[Issue]:
        """Obtener issues por estado"""
        return self.session.query(Issue).filter(Issue.status == status).all()
    
    def create_or_update(
        self,
        issue_data: Dict[str, Any],
        sonarcloud_project_id: int
    ) -> Issue:
        """
        Crear o actualizar issue
        
        Args:
            issue_data: Datos del issue desde SonarCloud
            sonarcloud_project_id: ID del proyecto de SonarCloud
            
        Returns:
            Issue creado o actualizado
        """
        # Buscar por clave primero
        existing = self.get_by_key(issue_data.get('key'))
        
        if existing:
            # Actualizar existente
            existing.update_from_sonarcloud_data(issue_data)
            self.session.commit()
            logger.debug(f"Issue actualizado - ID: {existing.id}, Key: {existing.key}")
            return existing
        else:
            # Crear nuevo
            new_issue = Issue.from_sonarcloud_data(issue_data, sonarcloud_project_id)
            self.session.add(new_issue)
            self.session.commit()
            logger.info(f"Nuevo issue creado - ID: {new_issue.id}, Key: {new_issue.key}, Project ID: {sonarcloud_project_id}")
            return new_issue


class SecurityHotspotRepository:
    """Repositorio para entidades SecurityHotspot"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, hotspot_id: int) -> Optional[SecurityHotspot]:
        """Obtener security hotspot por ID"""
        return self.session.query(SecurityHotspot).filter(SecurityHotspot.id == hotspot_id).first()
    
    def get_by_key(self, key: str) -> Optional[SecurityHotspot]:
        """Obtener security hotspot por clave"""
        return self.session.query(SecurityHotspot).filter(SecurityHotspot.key == key).first()
    
    def get_by_sonarcloud_id(self, sonarcloud_id: str) -> Optional[SecurityHotspot]:
        """Obtener security hotspot por ID de SonarCloud"""
        return self.session.query(SecurityHotspot).filter(SecurityHotspot.sonarcloud_id == sonarcloud_id).first()
    
    def get_by_project(self, sonarcloud_project_id: int) -> List[SecurityHotspot]:
        """Obtener security hotspots por proyecto"""
        return self.session.query(SecurityHotspot).filter(SecurityHotspot.sonarcloud_project_id == sonarcloud_project_id).all()
    
    def get_by_status(self, status: str) -> List[SecurityHotspot]:
        """Obtener security hotspots por estado"""
        return self.session.query(SecurityHotspot).filter(SecurityHotspot.status == status).all()
    
    def create_or_update(
        self,
        hotspot_data: Dict[str, Any],
        sonarcloud_project_id: int
    ) -> SecurityHotspot:
        """
        Crear o actualizar security hotspot
        
        Args:
            hotspot_data: Datos del security hotspot desde SonarCloud
            sonarcloud_project_id: ID del proyecto de SonarCloud
            
        Returns:
            SecurityHotspot creado o actualizado
        """
        # Buscar por clave primero
        existing = self.get_by_key(hotspot_data.get('key'))
        
        if existing:
            # Actualizar existente
            existing.update_from_sonarcloud_data(hotspot_data)
            self.session.commit()
            logger.debug(f"Security hotspot actualizado - ID: {existing.id}, Key: {existing.key}")
            return existing
        else:
            # Crear nuevo
            new_hotspot = SecurityHotspot.from_sonarcloud_data(hotspot_data, sonarcloud_project_id)
            self.session.add(new_hotspot)
            self.session.commit()
            logger.info(f"Nuevo security hotspot creado - ID: {new_hotspot.id}, Key: {new_hotspot.key}, Project ID: {sonarcloud_project_id}")
            return new_hotspot


class QualityGateRepository:
    """Repositorio para entidades QualityGate"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, quality_gate_id: int) -> Optional[QualityGate]:
        """Obtener quality gate por ID"""
        return self.session.query(QualityGate).filter(QualityGate.id == quality_gate_id).first()
    
    def get_by_key(self, key: str) -> Optional[QualityGate]:
        """Obtener quality gate por clave"""
        return self.session.query(QualityGate).filter(QualityGate.key == key).first()
    
    def get_by_project(self, sonarcloud_project_id: int) -> Optional[QualityGate]:
        """Obtener quality gate por proyecto"""
        return self.session.query(QualityGate).filter(QualityGate.sonarcloud_project_id == sonarcloud_project_id).first()
    
    def create_or_update(
        self,
        quality_gate_data: Dict[str, Any],
        sonarcloud_project_id: int
    ) -> QualityGate:
        """
        Crear o actualizar quality gate
        
        Args:
            quality_gate_data: Datos del quality gate desde SonarCloud
            sonarcloud_project_id: ID del proyecto de SonarCloud
            
        Returns:
            QualityGate creado o actualizado
        """
        # Buscar por proyecto primero
        existing = self.get_by_project(sonarcloud_project_id)
        
        if existing:
            # Actualizar existente
            existing.update_from_sonarcloud_data(quality_gate_data)
            self.session.commit()
            logger.debug(f"Quality gate actualizado - ID: {existing.id}, Project ID: {sonarcloud_project_id}")
            return existing
        else:
            # Crear nuevo
            new_quality_gate = QualityGate.from_sonarcloud_data(quality_gate_data, sonarcloud_project_id)
            self.session.add(new_quality_gate)
            self.session.commit()
            logger.info(f"Nuevo quality gate creado - ID: {new_quality_gate.id}, Project ID: {sonarcloud_project_id}")
            return new_quality_gate


class MetricRepository:
    """Repositorio para entidades Metric"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, metric_id: int) -> Optional[Metric]:
        """Obtener métrica por ID"""
        return self.session.query(Metric).filter(Metric.id == metric_id).first()
    
    def get_by_key(self, key: str) -> Optional[Metric]:
        """Obtener métrica por clave"""
        return self.session.query(Metric).filter(Metric.key == key).first()
    
    def get_by_project(self, sonarcloud_project_id: int) -> List[Metric]:
        """Obtener métricas por proyecto"""
        return self.session.query(Metric).filter(Metric.sonarcloud_project_id == sonarcloud_project_id).all()
    
    def create_or_update(
        self,
        metric_data: Dict[str, Any],
        sonarcloud_project_id: int
    ) -> Metric:
        """
        Crear o actualizar métrica
        
        Args:
            metric_data: Datos de la métrica desde SonarCloud
            sonarcloud_project_id: ID del proyecto de SonarCloud
            
        Returns:
            Metric creada o actualizada
        """
        # Buscar por clave y proyecto primero
        existing = self.session.query(Metric).filter(
            and_(
                Metric.key == metric_data.get('metric'),
                Metric.sonarcloud_project_id == sonarcloud_project_id
            )
        ).first()
        
        if existing:
            # Actualizar existente
            existing.update_from_sonarcloud_data(metric_data)
            self.session.commit()
            logger.debug(f"Métrica actualizada - ID: {existing.id}, Key: {existing.key}")
            return existing
        else:
            # Crear nueva
            new_metric = Metric.from_sonarcloud_data(metric_data, sonarcloud_project_id)
            self.session.add(new_metric)
            self.session.commit()
            logger.info(f"Nueva métrica creada - ID: {new_metric.id}, Key: {new_metric.key}, Project ID: {sonarcloud_project_id}")
            return new_metric
