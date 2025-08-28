#!/usr/bin/env python3
"""
Script para procesar todos los proyectos del workspace configurado

Este script obtiene todos los proyectos del workspace desde Bitbucket
y los guarda/actualiza en la base de datos PostgreSQL usando las funciones
centralizadas de RepositoryService con todas las bondades del procesamiento
avanzado (rate limiting, batching, pausas automáticas).
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional

# Agregar el directorio raíz del proyecto al path de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.api.bitbucket_client import BitbucketClient
from src.services.repository_service import RepositoryService
from src.database.connection import init_database, close_database
from src.utils.logger import get_logger
from src.config.settings import get_settings


async def main():
    """Función principal del script"""
    try:
        # Inicializar configuración
        settings = get_settings()
        logger = get_logger(__name__)
        
        logger.info("Iniciando procesamiento de proyectos del workspace")
        
        # Obtener workspace desde configuración o argumentos
        workspace_slug = settings.bitbucket_workspace
        
        if len(sys.argv) > 1:
            workspace_slug = sys.argv[1]
        
        logger.info(f"Workspace a procesar: {workspace_slug}")
        
        # Inicializar base de datos
        logger.info("Inicializando base de datos...")
        init_database()
        logger.info("Base de datos inicializada")
        
        # Inicializar cliente de Bitbucket
        logger.info("Inicializando cliente de Bitbucket...")
        bitbucket_client = BitbucketClient()
        logger.info("Cliente de Bitbucket inicializado")
        
        # Inicializar servicio de repositorios
        logger.info("Inicializando servicio de repositorios...")
        repository_service = RepositoryService(bitbucket_client)
        logger.info("Servicio de repositorios inicializado")
        
        # Obtener proyectos del workspace para mostrar resumen
        logger.info(f"Obteniendo proyectos del workspace: {workspace_slug}")
        projects = await bitbucket_client.get_all_workspace_projects(workspace_slug)
        
        if not projects:
            logger.warning(f"No se encontraron proyectos en el workspace: {workspace_slug}")
            return
        
        total_projects = len(projects)
        logger.info(f"Encontrados {total_projects} proyectos para procesar")
        
        # Mostrar resumen de proyectos
        print(f"\n📊 Resumen del Workspace: {workspace_slug}")
        print(f"Total de proyectos: {total_projects}")
        
        # Mostrar información básica de cada proyecto
        for i, project in enumerate(projects[:10], 1):  # Mostrar solo los primeros 10
            project_key = project.get('key', 'N/A')
            project_name = project.get('name', project_key)
            is_private = project.get('is_private', True)
            print(f"{i:2d}. {project_name} ({project_key})")
            print(f"     Privado: {'Sí' if is_private else 'No'}")
            print(f"     Descripción: {project.get('description', 'Sin descripción')}")
            print()
        
        if len(projects) > 10:
            print(f"... y {len(projects) - 10} proyectos más")
        
        # Preguntar si sincronizar con base de datos
        sync_choice = input("\n¿Desea sincronizar estos proyectos con la base de datos? (y/N): ")
        
        if sync_choice.lower() in ['y', 'yes']:
            logger.info("Iniciando sincronización con base de datos")
            
            # Sincronizar proyectos usando las funciones centralizadas
            sync_summary = await repository_service.sync_workspace_projects(
                workspace_slug, batch_size=10
            )
            
            print(f"\nSincronización completada")
            print(f"Proyectos procesados: {sync_summary['total_projects']}")
            print(f"Exitosos: {sync_summary['successful_syncs']}")
            print(f"Fallidos: {sync_summary['failed_syncs']}")
            print(f"Tasa de éxito: {sync_summary['success_rate']:.1f}%")
            print(f"Duración: {sync_summary['duration_seconds']:.1f} segundos")
            
            logger.info("Procesamiento completado exitosamente")
            logger.info("Los proyectos han sido guardados/actualizados en la base de datos")
        else:
            logger.info("Sincronización cancelada por el usuario")
        
    except Exception as e:
        logger.error(f"Error en el procesamiento: {str(e)}")
        sys.exit(1)
    
    finally:
        # Cerrar conexiones
        try:
            close_database()
            logger.info("Conexiones cerradas")
        except Exception as e:
            logger.error(f"Error al cerrar conexiones: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
