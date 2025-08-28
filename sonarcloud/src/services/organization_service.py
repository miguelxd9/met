"""
Servicio de organizaciones para SonarCloud

Proporciona lógica de negocio para el procesamiento y gestión
de organizaciones de SonarCloud.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..api.sonarcloud_client import SonarCloudClient
from ..database.repositories import OrganizationRepository
from ..models import Organization
from ..utils.logger import get_logger


class OrganizationService:
    """
    Servicio para gestión de organizaciones de SonarCloud
    
    Maneja la lógica de negocio para obtener, procesar y almacenar
    datos de organizaciones desde SonarCloud API.
    """
    
    def __init__(self):
        """Inicializar servicio de organizaciones"""
        self.client = SonarCloudClient()
        self.org_repo = OrganizationRepository()
        self.logger = get_logger(__name__)
        
        self.logger.info("Servicio de organizaciones inicializado")
    
    async def sync_organization(
        self,
        session: Session,
        organization_key: str
    ) -> Dict[str, Any]:
        """
        Sincronizar organización desde SonarCloud
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            
        Returns:
            Dict con resultado de la sincronización
        """
        try:
            self.logger.info(f"Sincronizando organización - Key: {organization_key}")
            
            # Obtener datos de la organización desde SonarCloud
            org_data = await self.client.get_organization(organization_key)
            
            # Buscar organización existente
            existing_org = self.org_repo.get_by_key(session, organization_key)
            
            if existing_org:
                # Actualizar organización existente
                existing_org.update_from_sonarcloud_data(org_data)
                session.flush()
                
                self.logger.info(f"Organización actualizada - Key: {organization_key}")
                return {'action': 'updated', 'organization': existing_org}
                
            else:
                # Crear nueva organización
                new_org = Organization.from_sonarcloud_data(org_data)
                session.add(new_org)
                session.flush()
                
                self.logger.info(f"Organización creada - Key: {organization_key}")
                return {'action': 'created', 'organization': new_org}
                
        except Exception as e:
            self.logger.error(f"Error al sincronizar organización {organization_key}: {str(e)}")
            raise
    
    def get_organization(
        self,
        session: Session,
        organization_key: str
    ) -> Optional[Organization]:
        """
        Obtener organización por clave
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            
        Returns:
            Organización encontrada o None
        """
        try:
            return self.org_repo.get_by_key(session, organization_key)
        except Exception as e:
            self.logger.error(f"Error al obtener organización {organization_key}: {str(e)}")
            raise
    
    def get_all_organizations(
        self,
        session: Session
    ) -> List[Organization]:
        """
        Obtener todas las organizaciones
        
        Args:
            session: Sesión de base de datos
            
        Returns:
            Lista de organizaciones
        """
        try:
            return self.org_repo.get_all(session)
        except Exception as e:
            self.logger.error(f"Error al obtener todas las organizaciones: {str(e)}")
            raise
    
    def get_organization_summary(
        self,
        session: Session,
        organization_key: str
    ) -> Dict[str, Any]:
        """
        Obtener resumen de una organización
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            
        Returns:
            Dict con resumen de la organización
        """
        try:
            organization = self.org_repo.get_by_key(session, organization_key)
            if not organization:
                raise ValueError(f"Organización no encontrada: {organization_key}")
            
            summary = {
                'key': organization.key,
                'name': organization.name,
                'description': organization.description,
                'is_private': organization.is_private,
                'is_default': organization.is_default,
                'metrics': organization.get_metrics_summary(),
                'created_at': organization.created_at.isoformat() if organization.created_at else None,
                'updated_at': organization.updated_at.isoformat() if organization.updated_at else None
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error al obtener resumen de organización {organization_key}: {str(e)}")
            raise
