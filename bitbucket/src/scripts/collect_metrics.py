"""
Script principal para recolección de métricas DevOps desde Bitbucket

Este script permite:
- Obtener métricas de un workspace completo
- Obtener métricas de un proyecto específico
- Obtener métricas de un repositorio específico
- Sincronizar datos con la base de datos
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.bitbucket_client import BitbucketClient
from src.services.repository_service import RepositoryService
from src.database.connection import init_database, close_database
from src.utils.logger import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


async def main():
    """Función principal del script"""
    try:
        # Inicializar configuración
        settings = get_settings()
        logger.info("Iniciando recolección de métricas DevOps")
        
        # Inicializar base de datos
        init_database()
        logger.info("Base de datos inicializada")
        
        # Inicializar cliente de Bitbucket
        bitbucket_client = BitbucketClient()
        logger.info("Cliente de Bitbucket inicializado")
        
        # Inicializar servicio de repositorios
        repository_service = RepositoryService(bitbucket_client)
        logger.info("Servicio de repositorios inicializado")
        
        # Obtener argumentos de línea de comandos
        workspace_slug = settings.bitbucket_workspace
        project_key = None
        
        if len(sys.argv) > 1:
            workspace_slug = sys.argv[1]
        
        if len(sys.argv) > 2:
            project_key = sys.argv[2]
        
        logger.info(
            "Parámetros de ejecución",
            workspace_slug=workspace_slug,
            project_key=project_key
        )
        
        # Ejecutar recolección según los parámetros
        if project_key:
            await collect_project_metrics(repository_service, workspace_slug, project_key)
        else:
            await collect_workspace_metrics(repository_service, workspace_slug)
        
        logger.info("Recolección de métricas completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error en la recolección de métricas: {str(e)}")
        sys.exit(1)
    
    finally:
        # Cerrar conexiones
        try:
            close_database()
            logger.info("Conexiones cerradas")
        except Exception as e:
            logger.error(f"Error al cerrar conexiones: {str(e)}")


async def collect_workspace_metrics(
    repository_service: RepositoryService,
    workspace_slug: str
):
    """
    Recolectar métricas de todo un workspace
    
    Args:
        repository_service: Servicio de repositorios
        workspace_slug: Slug del workspace
    """
    logger.info(f"Iniciando recolección de métricas del workspace: {workspace_slug}")
    
    try:
        # Obtener repositorios del workspace
        repositories = await repository_service.get_workspace_repositories(workspace_slug)
        
        logger.info(
            f"Repositorios obtenidos del workspace",
            workspace_slug=workspace_slug,
            total_repositories=len(repositories)
        )
        
        # Mostrar resumen de repositorios
        print(f"\n📊 Resumen del Workspace: {workspace_slug}")
        print(f"Total de repositorios: {len(repositories)}")
        
        # Mostrar información básica de cada repositorio
        for i, repo in enumerate(repositories[:10], 1):  # Mostrar solo los primeros 10
            print(f"{i:2d}. {repo.get('name', 'N/A')} ({repo.get('language', 'N/A')})")
            print(f"     Commits: {repo.get('commits_count', 0)}")
            print(f"     PRs: {repo.get('pull_requests_count', 0)}")
            print(f"     Tamaño: {repo.get('size', 0)} bytes")
            print()
        
        if len(repositories) > 10:
            print(f"... y {len(repositories) - 10} repositorios más")
        
        # Preguntar si sincronizar con base de datos
        sync_choice = input("\n¿Desea sincronizar estos repositorios con la base de datos? (y/N): ")
        
        if sync_choice.lower() in ['y', 'yes']:
            logger.info("Iniciando sincronización con base de datos")
            
            # Sincronizar repositorios
            sync_summary = await repository_service.sync_workspace_repositories(
                workspace_slug, batch_size=5
            )
            
            print(f"\n✅ Sincronización completada")
            print(f"Repositorios procesados: {sync_summary['total_repositories']}")
            print(f"Exitosos: {sync_summary['successful_syncs']}")
            print(f"Fallidos: {sync_summary['failed_syncs']}")
            print(f"Tasa de éxito: {sync_summary['success_rate']:.1f}%")
            print(f"Duración: {sync_summary['duration_seconds']:.1f} segundos")
        
    except Exception as e:
        logger.error(f"Error al recolectar métricas del workspace: {str(e)}")
        raise


async def collect_project_metrics(
    repository_service: RepositoryService,
    workspace_slug: str,
    project_key: str
):
    """
    Recolectar métricas de un proyecto específico
    
    Args:
        repository_service: Servicio de repositorios
        workspace_slug: Slug del workspace
        project_key: Clave del proyecto
    """
    logger.info(f"Iniciando recolección de métricas del proyecto: {project_key}")
    
    try:
        # Obtener repositorios del proyecto
        repositories = await repository_service.get_project_repositories(
            workspace_slug, project_key
        )
        
        logger.info(
            f"Repositorios obtenidos del proyecto",
            workspace_slug=workspace_slug,
            project_key=project_key,
            total_repositories=len(repositories)
        )
        
        # Mostrar resumen del proyecto
        print(f"\n📊 Resumen del Proyecto: {project_key}")
        print(f"Workspace: {workspace_slug}")
        print(f"Total de repositorios: {len(repositories)}")
        
        # Mostrar información básica de cada repositorio
        for i, repo in enumerate(repositories, 1):
            print(f"{i:2d}. {repo.get('name', 'N/A')} ({repo.get('language', 'N/A')})")
            print(f"     Commits: {repo.get('commits_count', 0)}")
            print(f"     PRs: {repo.get('pull_requests_count', 0)}")
            print(f"     Tamaño: {repo.get('size', 0)} bytes")
            print()
        
        # Preguntar si sincronizar con base de datos
        sync_choice = input("\n¿Desea sincronizar estos repositorios con la base de datos? (y/N): ")
        
        if sync_choice.lower() in ['y', 'yes']:
            logger.info("Iniciando sincronización con base de datos")
            
            # Sincronizar repositorios del proyecto
            for repo in repositories:
                try:
                    await repository_service.sync_repository_to_database(
                        workspace_slug, repo['slug'], project_key
                    )
                    print(f"✅ {repo['name']} sincronizado")
                except Exception as e:
                    print(f"❌ Error al sincronizar {repo['name']}: {str(e)}")
            
            print(f"\n✅ Sincronización del proyecto completada")
        
    except Exception as e:
        logger.error(f"Error al recolectar métricas del proyecto: {str(e)}")
        raise


async def collect_repository_metrics(
    repository_service: RepositoryService,
    workspace_slug: str,
    repository_slug: str
):
    """
    Recolectar métricas de un repositorio específico
    
    Args:
        repository_service: Servicio de repositorios
        workspace_slug: Slug del workspace
        repository_slug: Slug del repositorio
    """
    logger.info(f"Iniciando recolección de métricas del repositorio: {repository_slug}")
    
    try:
        # Obtener información del repositorio
        repository = await repository_service.get_repository(workspace_slug, repository_slug)
        
        if not repository:
            print(f"❌ Repositorio {repository_slug} no encontrado")
            return
        
        # Mostrar información del repositorio
        print(f"\n📊 Información del Repositorio: {repository['name']}")
        print(f"Slug: {repository['slug']}")
        print(f"Workspace: {workspace_slug}")
        print(f"Lenguaje: {repository.get('language', 'N/A')}")
        print(f"Privado: {'Sí' if repository.get('is_private') else 'No'}")
        print(f"Commits: {repository.get('commits_count', 0)}")
        print(f"Pull Requests: {repository.get('pull_requests_count', 0)}")
        print(f"Tamaño: {repository.get('size', 0)} bytes")
        
        if repository.get('description'):
            print(f"Descripción: {repository['description']}")
        
        # Preguntar si sincronizar con base de datos
        sync_choice = input("\n¿Desea sincronizar este repositorio con la base de datos? (y/N): ")
        
        if sync_choice.lower() in ['y', 'yes']:
            logger.info("Iniciando sincronización con base de datos")
            
            # Sincronizar repositorio
            try:
                sync_result = await repository_service.sync_repository_to_database(
                    workspace_slug, repository_slug
                )
                
                if sync_result:
                    print(f"\n✅ Repositorio sincronizado exitosamente")
                    print(f"ID en BD: {sync_result['id']}")
                    print(f"Total commits: {sync_result['total_commits']}")
                    print(f"Total PRs: {sync_result['total_pull_requests']}")
                    print(f"PRs abiertos: {sync_result['open_pull_requests']}")
                else:
                    print(f"❌ Error al sincronizar el repositorio")
                    
            except Exception as e:
                print(f"❌ Error durante la sincronización: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error al recolectar métricas del repositorio: {str(e)}")
        raise


def show_usage():
    """Mostrar información de uso del script"""
    print("""
🚀 Script de Recolección de Métricas DevOps - Bitbucket

Uso:
    python collect_metrics.py [workspace] [project]

Argumentos:
    workspace    Slug del workspace (opcional, usa configuración por defecto)
    project      Clave del proyecto (opcional)

Ejemplos:
    python collect_metrics.py                    # Usa configuración por defecto
    python collect_metrics.py mi-workspace      # Workspace específico
    python collect_metrics.py mi-workspace PROJ # Proyecto específico

Configuración:
    Asegúrate de tener configurado el archivo .env con:
    - BITBUCKET_USERNAME
    - BITBUCKET_APP_PASSWORD  
    - BITBUCKET_WORKSPACE
    - DATABASE_URL
    """)


if __name__ == "__main__":
    # Verificar argumentos de ayuda
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_usage()
        sys.exit(0)
    
    # Ejecutar script principal
    asyncio.run(main())
