#!/usr/bin/env python3
"""
Script principal para recolección de métricas de SonarCloud

Este script sincroniza datos de SonarCloud con la base de datos local,
incluyendo la vinculación automática con repositorios de Bitbucket.

Uso:
- Sin parámetros: Procesa todos los proyectos de la organización
- Con parámetros: collect_sonarcloud_metrics.py <workspace_slug> <project_key>
  Ejemplo: collect_sonarcloud_metrics.py interbank tunki
"""

import asyncio
import sys
import os
from typing import List, Dict, Any, Optional

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.sonarcloud_client import SonarCloudClient
from src.services.sonarcloud_service import SonarCloudService
from src.config.settings import get_settings
from src.utils.logger import get_logger
from src.database.connection import init_database, get_session
from src.models.project import Project
from src.models.repository import Repository
from src.models.sonarcloud_project import SonarCloudProject

logger = get_logger(__name__)


def get_sonarcloud_projects_by_bitbucket_project(project_key: str) -> List[str]:
    """
    Obtiene los keys de SonarCloud para un proyecto específico de Bitbucket
    
    Args:
        project_key: Key del proyecto de Bitbucket
        
    Returns:
        Lista de keys de SonarCloud vinculados al proyecto
    """
    try:
        session = get_session()
        
        # 1. Buscar el proyecto por key
        project = session.query(Project).filter(Project.key == project_key).first()
        if not project:
            logger.warning(f"No se encontró el proyecto con key: {project_key}")
            return []
        
        project_id = project.id
        logger.info(f"Proyecto encontrado: {project.name} (ID: {project_id})")
        
        # 2. Obtener repositorios del proyecto
        repositories = session.query(Repository).filter(Repository.project_id == project_id).all()
        if not repositories:
            logger.warning(f"No se encontraron repositorios para el proyecto: {project_key}")
            return []
        
        repository_ids = [repo.id for repo in repositories]
        logger.info(f"Repositorios encontrados: {len(repositories)}")
        
        # 3. Buscar proyectos de SonarCloud vinculados a estos repositorios
        sonarcloud_projects = session.query(SonarCloudProject).filter(
            SonarCloudProject.bitbucket_repository_id.in_(repository_ids)
        ).all()
        
        if not sonarcloud_projects:
            logger.warning(f"No se encontraron proyectos de SonarCloud vinculados al proyecto: {project_key}")
            return []
        
        project_keys = [scp.key for scp in sonarcloud_projects]
        logger.info(f"Proyectos de SonarCloud vinculados: {len(project_keys)}")
        
        return project_keys
        
    except Exception as e:
        logger.error(f"Error obteniendo proyectos de SonarCloud para {project_key}: {str(e)}")
        return []
    finally:
        if 'session' in locals():
            session.close()


async def main():
    """Función principal del script"""
    
    try:
        # Verificar argumentos de línea de comandos
        if len(sys.argv) == 3:
            # Modo específico: collect_sonarcloud_metrics.py <workspace_slug> <project_key>
            workspace_slug = sys.argv[1]
            project_key = sys.argv[2]
            specific_mode = True
            logger.info("=" * 60)
            logger.info("MODO ESPECÍFICO: Procesando proyecto específico")
            logger.info("=" * 60)
            logger.info(f"Workspace: {workspace_slug}")
            logger.info(f"Proyecto: {project_key}")
            logger.info("=" * 60)
        elif len(sys.argv) == 1:
            # Modo general: collect_sonarcloud_metrics.py (sin parámetros)
            specific_mode = False
            logger.info("=" * 60)
            logger.info("MODO GENERAL: Procesando todos los proyectos")
            logger.info("=" * 60)
        else:
            logger.error("ERROR: Uso incorrecto del script")
            logger.error("Uso:")
            logger.error("  Sin parámetros: python src/scripts/collect_sonarcloud_metrics.py")
            logger.error("  Con parámetros: python src/scripts/collect_sonarcloud_metrics.py <workspace_slug> <project_key>")
            logger.error("Ejemplo: python src/scripts/collect_sonarcloud_metrics.py interbank tunki")
            return 1
        
        # Obtener configuración
        settings = get_settings()
        organization_key = settings.sonarcloud_organization
        
        logger.info("Iniciando recolección AUTOMÁTICA de métricas de SonarCloud")
        logger.info(f"Organización: {organization_key}")
        
        # Inicializar base de datos
        logger.info("Inicializando base de datos...")
        init_database()
        logger.info("Base de datos inicializada exitosamente")
        
        # Inicializar cliente y servicio
        sonarcloud_client = SonarCloudClient()
        sonarcloud_service = SonarCloudService(sonarcloud_client)
        
        # Verificar conexión con SonarCloud
        logger.info("Verificando conexión con SonarCloud...")
        organization_info = await sonarcloud_client.get_organization(organization_key)
        
        if not organization_info:
            logger.error(f"ERROR: No se pudo conectar con SonarCloud para la organización: {organization_key}")
            logger.error("Verifica que el token de SonarCloud sea válido y la organización exista")
            return 1
        
        logger.info(f"CONEXION EXITOSA con SonarCloud")
        logger.info(f"Organización: {organization_info.get('name', 'N/A')}")
        logger.info(f"Clave: {organization_info.get('key', 'N/A')}")
        
        if specific_mode:
            # MODO ESPECÍFICO: Procesar solo proyectos del proyecto de Bitbucket especificado
            logger.info(f"Obteniendo proyectos de SonarCloud vinculados al proyecto: {project_key}")
            
            # Obtener keys de SonarCloud para el proyecto específico
            sonarcloud_project_keys = get_sonarcloud_projects_by_bitbucket_project(project_key)
            
            if not sonarcloud_project_keys:
                logger.error(f"No se encontraron proyectos de SonarCloud vinculados al proyecto: {project_key}")
                logger.error("Asegúrate de que:")
                logger.error("1. El proyecto existe en Bitbucket")
                logger.error("2. Los repositorios están vinculados con proyectos de SonarCloud")
                logger.error("3. Se ejecutó previamente el script de vinculación")
                return 1
            
            logger.info(f"Proyectos de SonarCloud a procesar: {len(sonarcloud_project_keys)}")
            
            # Mostrar información de los proyectos a procesar
            logger.info("Proyectos que se procesarán:")
            for i, key in enumerate(sonarcloud_project_keys, 1):
                logger.info(f"  {i:2d}. {key}")
            
            # Procesar solo los proyectos específicos
            logger.info("Iniciando procesamiento de proyectos específicos...")
            
            successful_syncs = 0
            failed_syncs = 0
            start_time = asyncio.get_event_loop().time()
            
            for i, project_key_sonarcloud in enumerate(sonarcloud_project_keys, 1):
                try:
                    logger.info(f"Procesando proyecto {i}/{len(sonarcloud_project_keys)}: {project_key_sonarcloud}")
                    
                    # Sincronizar proyecto específico
                    await sonarcloud_service.sync_project_details(project_key_sonarcloud)
                    successful_syncs += 1
                    logger.info(f"✅ Proyecto {project_key_sonarcloud} procesado exitosamente")
                    
                except Exception as e:
                    failed_syncs += 1
                    logger.error(f"❌ Error procesando proyecto {project_key_sonarcloud}: {str(e)}")
                    continue
            
            # Calcular tiempo total
            duration = asyncio.get_event_loop().time() - start_time
            
            # Mostrar resumen del modo específico
            logger.info("=" * 60)
            logger.info("PROCESAMIENTO ESPECÍFICO COMPLETADO")
            logger.info("=" * 60)
            logger.info(f"Proyecto de Bitbucket: {project_key}")
            logger.info(f"Proyectos de SonarCloud procesados: {len(sonarcloud_project_keys)}")
            logger.info(f"Sincronizaciones exitosas: {successful_syncs}")
            logger.info(f"Sincronizaciones fallidas: {failed_syncs}")
            logger.info(f"Tasa de éxito: {(successful_syncs / len(sonarcloud_project_keys) * 100):.1f}%")
            logger.info(f"Duración: {duration:.2f} segundos")
            logger.info("=" * 60)
            
        else:
            # MODO GENERAL: Procesar todos los proyectos de la organización
            logger.info("Obteniendo lista de proyectos de la organización...")
            projects = await sonarcloud_client.get_all_organization_projects(organization_key)
            
            if not projects:
                logger.warning(f"ADVERTENCIA: No se encontraron proyectos en la organización: {organization_key}")
                return 0
            
            logger.info(f"Proyectos encontrados: {len(projects)}")
            
            # Mostrar información básica de los primeros 5 proyectos
            logger.info("Información básica de los primeros 5 proyectos:")
            for i, project in enumerate(projects[:5], 1):
                logger.info(f"  {i:2d}. {project.get('name', 'N/A')} ({project.get('key', 'N/A')})")
                logger.info(f"      Visibilidad: {project.get('visibility', 'N/A')}")
                logger.info(f"      Qualifier: {project.get('qualifier', 'N/A')}")
            
            if len(projects) > 5:
                logger.info(f"  ... y {len(projects) - 5} proyectos más")
            
            # Iniciar sincronización automáticamente
            logger.info(f"Se encontraron {len(projects)} proyectos en SonarCloud")
            logger.info("Iniciando sincronización automática de proyectos...")
            logger.info("El proceso se ejecutará automáticamente sin interrupciones")
            
            # Configurar tamaño de lote
            batch_size = min(50, max(10, len(projects) // 20))  # Ajustar automáticamente
            logger.info(f"Tamaño de lote configurado: {batch_size} proyectos por lote")
            logger.info("Procesando proyectos en lotes para optimizar rendimiento...")
            
            sync_summary = await sonarcloud_service.sync_organization_projects(
                organization_key, 
                batch_size=batch_size
            )
            
            # Mostrar resumen de la sincronización
            logger.info("Sincronización completada!")
            logger.info(f"Resumen de la sincronización:")
            logger.info(f"  Total de proyectos: {sync_summary['total_projects']}")
            logger.info(f"  Sincronizaciones exitosas: {sync_summary['successful_syncs']}")
            logger.info(f"  Sincronizaciones fallidas: {sync_summary['failed_syncs']}")
            logger.info(f"  Tasa de éxito: {sync_summary['success_rate']:.1f}%")
            logger.info(f"  Duración: {sync_summary['duration_seconds']:.2f} segundos")
            
            # Mostrar algunos proyectos sincronizados como ejemplo
            if sync_summary['successful_syncs'] > 0:
                logger.info("\nEjemplos de proyectos sincronizados:")
                
                with sonarcloud_service.sonarcloud_client._make_request('GET', 'projects/search', {
                    'organization': organization_key,
                    'ps': 5
                }) as response:
                    sample_projects = response.get('components', [])
                    
                    for i, project in enumerate(sample_projects, 1):
                        project_summary = await sonarcloud_service.get_project_summary(project['key'])
                        if project_summary:
                            logger.info(f"  {i}. {project_summary['name']} ({project_summary['key']})")
                            logger.info(f"     Estado Quality Gate: {project_summary['quality_gate_status'] or 'N/A'}")
                            logger.info(f"     Métricas: {project_summary['metrics_count']} metrics")
                            logger.info(f"     Vinculado con Bitbucket: {'Sí' if project_summary['bitbucket_repository_id'] else 'No'}")
                            logger.info("")  # Línea en blanco para separar proyectos
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nSincronización interrumpida por el usuario")
        return 1
        
    except Exception as e:
        logger.error(f"ERROR: Error inesperado durante la sincronización: {str(e)}")
        logger.exception("Detalles del error:")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"ERROR FATAL: {str(e)}")
        sys.exit(1)
