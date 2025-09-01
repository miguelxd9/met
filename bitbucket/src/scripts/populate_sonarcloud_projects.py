#!/usr/bin/env python3
"""
Script para poblar la tabla sonarcloud_projects con datos básicos de SonarCloud

Este script:
1. Se conecta a la API de SonarCloud
2. Obtiene todos los proyectos de la organización
3. Pobla la tabla sonarcloud_projects con datos básicos
4. NO consulta detalles individuales de proyectos
5. Respeta rate limiting y buenas prácticas del proyecto

Uso:
python src/scripts/populate_sonarcloud_projects.py
"""

import asyncio
import sys
import os
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_session, init_database
from src.api.sonarcloud_client import SonarCloudClient
from src.database.sonarcloud_repositories import SonarCloudProjectRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def populate_sonarcloud_projects() -> Dict[str, Any]:
    """
    Pobla la tabla sonarcloud_projects con datos básicos de SonarCloud
    
    Returns:
        Diccionario con el resumen de la operación
    """
    start_time = time.time()
    total_projects = 0
    created_count = 0
    updated_count = 0
    error_count = 0
    
    try:
        # Inicializar base de datos
        logger.info("Inicializando base de datos...")
        init_database()
        
        # Obtener sesión de base de datos
        session = get_session()
        
        # Inicializar cliente de SonarCloud
        logger.info("Inicializando cliente de SonarCloud...")
        client = SonarCloudClient()
        
        # Verificar conexión
        logger.info("Verificando conexión con SonarCloud...")
        try:
            # Intentar obtener un proyecto para verificar la conexión
            test_projects = await client.get_all_organization_projects(ps=1)
            if not test_projects:
                raise Exception("No se pudieron obtener proyectos de prueba")
            logger.info("Conexión con SonarCloud verificada exitosamente")
        except Exception as e:
            logger.error(f"Error al verificar conexión con SonarCloud: {str(e)}")
            return {
                'success': False,
                'error': f'Error de conexión: {str(e)}',
                'total_projects': 0,
                'created_count': 0,
                'updated_count': 0,
                'error_count': 0,
                'duration_seconds': time.time() - start_time
            }
        
        # Obtener todos los proyectos de SonarCloud
        logger.info("Obteniendo todos los proyectos de SonarCloud...")
        projects_data = await client.get_all_organization_projects()
        
        if not projects_data:
            logger.warning("No se encontraron proyectos en SonarCloud")
            return {
                'success': True,
                'message': 'No hay proyectos para procesar',
                'total_projects': 0,
                'created_count': 0,
                'updated_count': 0,
                'error_count': 0,
                'duration_seconds': time.time() - start_time
            }
        
        total_projects = len(projects_data)
        logger.info(f"Proyectos encontrados en SonarCloud: {total_projects}")
        
        # Inicializar repositorio
        project_repo = SonarCloudProjectRepository(session)
        
        # Procesar cada proyecto
        logger.info("Iniciando procesamiento de proyectos...")
        
        for i, project_data in enumerate(projects_data, 1):
            try:
                logger.debug(f"Procesando proyecto {i}/{total_projects}: {project_data.get('key', 'N/A')}")
                
                # Crear o actualizar proyecto en la base de datos
                result = project_repo.create_or_update(project_data)
                
                if result['action'] == 'created':
                    created_count += 1
                    logger.debug(f"CREADO: {project_data.get('key', 'N/A')}")
                elif result['action'] == 'updated':
                    updated_count += 1
                    logger.debug(f"ACTUALIZADO: {project_data.get('key', 'N/A')}")
                else:
                    logger.debug(f"SIN CAMBIOS: {project_data.get('key', 'N/A')}")
                
                # Log de progreso cada 100 proyectos
                if i % 100 == 0:
                    logger.info(f"Progreso: {i}/{total_projects} proyectos procesados")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error procesando proyecto '{project_data.get('key', 'N/A')}': {str(e)}")
                continue
        
        # Calcular tiempo total
        duration = time.time() - start_time
        
        # Resumen final
        logger.info("=" * 60)
        logger.info("POBLACIÓN DE SONARCLOUD PROJECTS COMPLETADA")
        logger.info("=" * 60)
        logger.info(f"Total de proyectos en SonarCloud: {total_projects}")
        logger.info(f"Proyectos creados: {created_count}")
        logger.info(f"Proyectos actualizados: {updated_count}")
        logger.info(f"Errores encontrados: {error_count}")
        logger.info(f"Tiempo de ejecución: {duration:.2f} segundos")
        logger.info("=" * 60)
        
        return {
            'success': True,
            'total_projects': total_projects,
            'created_count': created_count,
            'updated_count': updated_count,
            'error_count': error_count,
            'duration_seconds': duration
        }
        
    except Exception as e:
        logger.error(f"ERROR durante la población: {str(e)}")
        logger.exception("Detalles del error:")
        return {
            'success': False,
            'error': str(e),
            'total_projects': total_projects,
            'created_count': created_count,
            'updated_count': updated_count,
            'error_count': error_count,
            'duration_seconds': time.time() - start_time
        }
    
    finally:
        if 'session' in locals():
            session.close()


async def main():
    """Función principal del script"""
    
    logger.info("=" * 60)
    logger.info("SCRIPT DE POBLACIÓN SONARCLOUD PROJECTS")
    logger.info("=" * 60)
    logger.info("Iniciando proceso de población masiva...")
    logger.info("=" * 60)
    
    try:
        # Ejecutar población
        result = await populate_sonarcloud_projects()
        
        if result['success']:
            logger.info("✅ POBLACIÓN EXITOSA")
            logger.info(f"📊 Resumen: {result['total_projects']} proyectos procesados")
            logger.info(f"🆕 Creados: {result['created_count']}")
            logger.info(f"🔄 Actualizados: {result['updated_count']}")
            logger.info(f"⚠️ Errores: {result['error_count']}")
            logger.info(f"⏱️ Tiempo: {result['duration_seconds']:.2f} segundos")
            return 0
        else:
            logger.error(f"❌ POBLACIÓN FALLIDA: {result.get('error', 'Error desconocido')}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\nPoblación interrumpida por el usuario")
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
