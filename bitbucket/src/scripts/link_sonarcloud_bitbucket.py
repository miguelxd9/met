#!/usr/bin/env python3
"""
Script para vincular automáticamente proyectos de SonarCloud con repositorios de Bitbucket

Este script:
1. Obtiene el project_id desde la tabla projects usando project_key
2. Obtiene repositorios relacionados desde la tabla repositories
3. Obtiene todos los proyectos de SonarCloud
4. Compara el slug del repositorio con la parte final del key de SonarCloud
5. Actualiza la tabla sonarcloud_projects con bitbucket_repository_id

Uso:
python src/scripts/link_sonarcloud_bitbucket.py <workspace_slug> <project_key>
"""

import asyncio
import sys
import os
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_session, init_database
from src.models.project import Project
from src.models.repository import Repository
from src.models.sonarcloud_project import SonarCloudProject
from src.utils.logger import get_logger

logger = get_logger(__name__)


def extract_repository_name_from_sonarcloud_key(sonarcloud_key: str) -> Optional[str]:
    """
    Extrae el nombre del repositorio del key de SonarCloud
    
    Args:
        sonarcloud_key: Key de SonarCloud (ej: 'aad-pe.interbank.channel.aad.aaddigitaluserlock:aad-digital-user-lock')
        
    Returns:
        Nombre del repositorio extraído (ej: 'aad-digital-user-lock') o None si no se puede extraer
    """
    try:
        # Buscar el último ":" en el key
        if ':' in sonarcloud_key:
            # Obtener la parte después del último ":"
            repository_name = sonarcloud_key.split(':')[-1]
            return repository_name
        return None
    except Exception as e:
        logger.warning(f"No se pudo extraer nombre del repositorio del key '{sonarcloud_key}': {str(e)}")
        return None


async def link_sonarcloud_bitbucket(workspace_slug: str, project_key: str) -> Dict[str, Any]:
    """
    Vincula proyectos de SonarCloud con repositorios de Bitbucket
    
    Args:
        workspace_slug: Slug del workspace de Bitbucket
        project_key: Key del proyecto de Bitbucket
        
    Returns:
        Diccionario con el resumen de la operación
    """
    start_time = time.time()
    updated_count = 0
    total_sonarcloud_projects = 0
    
    try:
        # Inicializar base de datos
        logger.info("Inicializando base de datos...")
        init_database()
        
        # Obtener sesión de base de datos
        session = get_session()
        
        # 1. Obtener project_id desde la tabla projects usando project_key
        logger.info(f"Buscando proyecto con key: {project_key}")
        project = session.query(Project).filter(Project.key == project_key).first()
        
        if not project:
            logger.error(f"ERROR: No se encontró el proyecto con key '{project_key}'")
            return {
                'success': False,
                'error': f'Proyecto no encontrado: {project_key}',
                'updated_count': 0,
                'duration_seconds': time.time() - start_time
            }
        
        project_id = project.id
        logger.info(f"Proyecto encontrado - ID: {project_id}, Nombre: {project.name}")
        
        # 2. Obtener repositorios relacionados desde la tabla repositories filtrados por project_id
        logger.info(f"Obteniendo repositorios del proyecto {project_key}...")
        repositories = session.query(Repository).filter(Repository.project_id == project_id).all()
        
        if not repositories:
            logger.warning(f"ADVERTENCIA: No se encontraron repositorios para el proyecto '{project_key}'")
            return {
                'success': True,
                'message': f'No hay repositorios para vincular en el proyecto {project_key}',
                'updated_count': 0,
                'duration_seconds': time.time() - start_time
            }
        
        logger.info(f"Repositorios encontrados: {len(repositories)}")
        
        # Crear diccionario de repositorios para búsqueda rápida
        repository_map = {}
        for repo in repositories:
            repository_map[repo.slug] = repo.id
            logger.debug(f"Repositorio: {repo.slug} (ID: {repo.id})")
        
        # 3. Obtener todos los proyectos de SonarCloud para búsqueda eficiente
        logger.info("Obteniendo proyectos de SonarCloud para búsqueda...")
        sonarcloud_projects = session.query(SonarCloudProject.key).all()
        total_sonarcloud_projects = len(sonarcloud_projects)
        
        if not sonarcloud_projects:
            logger.warning("ADVERTENCIA: No se encontraron proyectos en SonarCloud")
            return {
                'success': True,
                'message': 'No hay proyectos de SonarCloud para vincular',
                'updated_count': 0,
                'duration_seconds': time.time() - start_time
            }
        
        logger.info(f"Proyectos de SonarCloud disponibles: {total_sonarcloud_projects}")
        
        # Crear diccionario inverso: nombre_repositorio -> [sonarcloud_keys]
        # OPTIMIZACIÓN: Esto se hace una sola vez, no en cada iteración
        sonarcloud_repository_map = {}
        for sonarcloud_project in sonarcloud_projects:
            sonarcloud_key = sonarcloud_project.key
            repository_name = extract_repository_name_from_sonarcloud_key(sonarcloud_key)
            
            if repository_name:
                if repository_name not in sonarcloud_repository_map:
                    sonarcloud_repository_map[repository_name] = []
                sonarcloud_repository_map[repository_name].append(sonarcloud_key)
        
        logger.info(f"Repositorios únicos encontrados en SonarCloud: {len(sonarcloud_repository_map)}")
        
        # 4. BUCLE OPTIMIZADO: Iterar sobre repositorios de Bitbucket (5-20 iteraciones)
        # En lugar de iterar sobre TODOS los proyectos de SonarCloud (1103+ iteraciones)
        logger.info("Iniciando proceso de vinculación optimizado...")
        
        for repository in repositories:
            repository_slug = repository.slug
            bitbucket_repository_id = repository.id
            
            logger.debug(f"Procesando repositorio: {repository_slug} (ID: {bitbucket_repository_id})")
            
            # Buscar si existe un proyecto de SonarCloud que coincida con este repositorio
            if repository_slug in sonarcloud_repository_map:
                sonarcloud_keys = sonarcloud_repository_map[repository_slug]
                
                for sonarcloud_key in sonarcloud_keys:
                    try:
                        # Obtener el proyecto completo para actualizarlo
                        sonarcloud_project_full = session.query(SonarCloudProject).filter(
                            SonarCloudProject.key == sonarcloud_key
                        ).first()
                        
                        if sonarcloud_project_full:
                            # Verificar si ya está vinculado
                            if sonarcloud_project_full.bitbucket_repository_id != bitbucket_repository_id:
                                sonarcloud_project_full.bitbucket_repository_id = bitbucket_repository_id
                                session.commit()
                                updated_count += 1
                                logger.info(f"VINCULADO: '{sonarcloud_key}' -> Repositorio '{repository_slug}' (ID: {bitbucket_repository_id})")
                            else:
                                logger.debug(f"Ya vinculado: '{sonarcloud_key}' -> Repositorio '{repository_slug}'")
                        else:
                            logger.warning(f"No se pudo encontrar el proyecto completo de SonarCloud: {sonarcloud_key}")
                            
                    except Exception as e:
                        logger.error(f"Error al actualizar proyecto '{sonarcloud_key}': {str(e)}")
                        session.rollback()
            else:
                logger.debug(f"No se encontró proyecto de SonarCloud para el repositorio: '{repository_slug}'")
        
        # Calcular tiempo total
        duration = time.time() - start_time
        
        # Resumen final
        logger.info("=" * 60)
        logger.info("VINCULACIÓN COMPLETADA")
        logger.info("=" * 60)
        logger.info(f"Proyecto analizado: {project_key}")
        logger.info(f"Repositorios procesados: {len(repositories)}")
        logger.info(f"Proyectos de SonarCloud disponibles: {total_sonarcloud_projects}")
        logger.info(f"Repositorios únicos en SonarCloud: {len(sonarcloud_repository_map)}")
        logger.info(f"Proyectos actualizados: {updated_count}")
        logger.info(f"Tiempo de ejecución: {duration:.2f} segundos")
        logger.info("=" * 60)
        
        return {
            'success': True,
            'project_key': project_key,
            'repositories_count': len(repositories),
            'sonarcloud_projects_count': total_sonarcloud_projects,
            'sonarcloud_repositories_unique': len(sonarcloud_repository_map),
            'updated_count': updated_count,
            'duration_seconds': duration
        }
        
    except Exception as e:
        logger.error(f"ERROR durante la vinculación: {str(e)}")
        logger.exception("Detalles del error:")
        return {
            'success': False,
            'error': str(e),
            'updated_count': updated_count,
            'duration_seconds': time.time() - start_time
        }
    
    finally:
        if 'session' in locals():
            session.close()


async def main():
    """Función principal del script"""
    
    # Verificar argumentos
    if len(sys.argv) != 3:
        logger.error("ERROR: Uso incorrecto del script")
        logger.error("Uso: python src/scripts/link_sonarcloud_bitbucket.py <workspace_slug> <project_key>")
        logger.error("Ejemplo: python src/scripts/link_sonarcloud_bitbucket.py ibkteam mmp-plin")
        return 1
    
    workspace_slug = sys.argv[1]
    project_key = sys.argv[2]
    
    logger.info("=" * 60)
    logger.info("SCRIPT DE VINCULACIÓN SONARCLOUD-BITBUCKET")
    logger.info("=" * 60)
    logger.info(f"Workspace: {workspace_slug}")
    logger.info(f"Proyecto: {project_key}")
    logger.info("=" * 60)
    
    try:
        # Ejecutar vinculación
        result = await link_sonarcloud_bitbucket(workspace_slug, project_key)
        
        if result['success']:
            logger.info("✅ VINCULACIÓN EXITOSA")
            return 0
        else:
            logger.error(f"❌ VINCULACIÓN FALLIDA: {result.get('error', 'Error desconocido')}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\nVinculación interrumpida por el usuario")
        return 1
        
    except Exception as e:
        logger.error(f"ERROR FATAL: {str(e)}")
        logger.exception("Detalles del error:")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"ERROR FATAL: {str(e)}")
        sys.exit(1)
