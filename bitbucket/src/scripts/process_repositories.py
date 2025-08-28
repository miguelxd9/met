#!/usr/bin/env python3
"""
Script para procesar y guardar repositorios en la base de datos usando configuración JSON

Este script lee la configuración de repositorios desde config/repositories.json,
obtiene información detallada de cada uno desde Bitbucket y los guarda
en la base de datos PostgreSQL usando el mismo sistema avanzado que collect_metrics.py.

Características:
- Procesamiento en lotes (batch processing)
- Rate limiting inteligente
- Pausas automáticas entre lotes
- Manejo robusto de errores
- Sincronización completa de repositorios
"""

import asyncio
import sys
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.bitbucket_client import BitbucketClient
from src.services.repository_service import RepositoryService
from src.database.connection import init_database, close_database
from src.utils.logger import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


class RepositoryProcessor:
    """
    Clase para procesar repositorios usando el sistema avanzado de collect_metrics.py
    pero con configuración desde archivo JSON
    """
    
    def __init__(self):
        """Inicializar el procesador de repositorios"""
        self.settings = get_settings()
        self.bitbucket_client = BitbucketClient()
        self.repository_service = RepositoryService(self.bitbucket_client)
        
        # Estadísticas de procesamiento
        self.stats = {
            'total_repositories': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'errors': []
        }
    
    async def load_repositories_config(self, config_file: str = "config/repositories.json") -> List[Dict[str, Any]]:
        """
        Cargar configuración de repositorios desde archivo JSON
        
        Args:
            config_file: Ruta del archivo de configuración
            
        Returns:
            Lista de repositorios a procesar
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            repositories = config.get('repositories', [])
            
            logger.info(f"Configuración cargada desde: {config_file}")
            logger.info(f"Total de repositorios configurados: {len(repositories)}")
            
            print(f"📋 Configuración cargada desde: {config_file}")
            print(f"   📊 Total de repositorios: {len(repositories)}")
            print()
            
            return repositories
            
        except FileNotFoundError:
            error_msg = f"No se encontró el archivo de configuración: {config_file}"
            logger.error(error_msg)
            print(f"❌ Error: {error_msg}")
            return []
        except json.JSONDecodeError as e:
            error_msg = f"El archivo JSON no es válido: {e}"
            logger.error(error_msg)
            print(f"❌ Error: {error_msg}")
            return []
        except Exception as e:
            error_msg = f"Error al cargar configuración: {e}"
            logger.error(error_msg)
            print(f"❌ Error: {error_msg}")
            return []
    
    async def process_repositories_batch(
        self,
        repositories: List[Dict[str, Any]],
        batch_size: int = 5
    ) -> Dict[str, Any]:
        """
        Procesar repositorios en lotes usando el sistema de collect_metrics.py
        
        Args:
            repositories: Lista de repositorios a procesar
            batch_size: Tamaño del lote para procesamiento
            
        Returns:
            Resumen del procesamiento
        """
        logger.info(f"Iniciando procesamiento de repositorios en lotes - Total: {len(repositories)}, Batch size: {batch_size}")
        
        start_time = asyncio.get_event_loop().time()
        total_repositories = len(repositories)
        successful_syncs = 0
        failed_syncs = 0
        
        try:
            # Procesar en lotes
            for i in range(0, total_repositories, batch_size):
                batch = repositories[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_repositories + batch_size - 1) // batch_size
                
                logger.info(f"Procesando lote de repositorios - Batch: {batch_num}/{total_batches}, Size: {len(batch)}")
                print(f"📦 Procesando lote {batch_num}/{total_batches} ({len(batch)} repositorios)")
                
                for repo_config in batch:
                    try:
                        workspace_slug = repo_config.get('workspace_slug')
                        repository_slug = repo_config.get('repository_slug')
                        project_key = repo_config.get('project_key')
                        
                        print(f"   🔍 Procesando: {repository_slug} (Workspace: {workspace_slug})")
                        
                        # Usar el mismo método que collect_metrics.py
                        await self.repository_service.sync_repository_to_database(
                            workspace_slug, repository_slug, project_key
                        )
                        
                        print(f"   ✅ {repository_slug} sincronizado exitosamente")
                        successful_syncs += 1
                        
                    except Exception as e:
                        error_msg = f"Error al sincronizar {repository_slug}: {str(e)}"
                        logger.error(error_msg)
                        print(f"   ❌ {error_msg}")
                        failed_syncs += 1
                        self.stats['errors'].append(error_msg)
                
                # Pausa entre lotes (igual que collect_metrics.py)
                if i + batch_size < total_repositories:
                    logger.info(f"Pausa entre lotes - Batch: {batch_num}")
                    print(f"   ⏳ Pausa entre lotes...")
                    await asyncio.sleep(1)  # 1 segundo entre lotes
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # Actualizar estadísticas
            self.stats.update({
                'total_repositories': total_repositories,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs
            })
            
            sync_summary = {
                'total_repositories': total_repositories,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'success_rate': (successful_syncs / total_repositories * 100) if total_repositories > 0 else 0,
                'duration_seconds': duration,
                'errors': self.stats['errors']
            }
            
            logger.info(f"Procesamiento de repositorios completado - Summary: {sync_summary}")
            
            return sync_summary
            
        except Exception as e:
            error_msg = f"Error en procesamiento de repositorios: {str(e)}"
            logger.error(error_msg)
            raise
    
    async def process_all_repositories(self, config_file: str = "config/repositories.json") -> bool:
        """
        Procesar todos los repositorios configurados usando el sistema avanzado
        
        Args:
            config_file: Ruta del archivo de configuración
            
        Returns:
            True si se procesaron exitosamente
        """
        logger.info("Iniciando procesamiento de repositorios con sistema avanzado")
        
        print("🚀 Procesador de Repositorios Avanzado")
        print("=" * 60)
        print()
        
        try:
            # Inicializar base de datos
            print("🗄️  Inicializando base de datos...")
            init_database()
            logger.info("Base de datos inicializada")
            print("✅ Base de datos inicializada")
            
            # Cargar configuración
            print("📋 Cargando configuración de repositorios...")
            repositories = await self.load_repositories_config(config_file)
            
            if not repositories:
                print("❌ No se encontraron repositorios para procesar")
                return False
            
            # Mostrar resumen de repositorios
            print(f"\n📊 Resumen de Repositorios a Procesar")
            print(f"Total de repositorios: {len(repositories)}")
            
            # Mostrar información básica de cada repositorio
            for i, repo in enumerate(repositories[:10], 1):  # Mostrar solo los primeros 10
                workspace = repo.get('workspace_slug', 'N/A')
                repository = repo.get('repository_slug', 'N/A')
                project = repo.get('project_key', 'N/A')
                print(f"{i:2d}. {repository} (Workspace: {workspace}, Project: {project})")
            
            if len(repositories) > 10:
                print(f"... y {len(repositories) - 10} repositorios más")
            
            # Preguntar si procesar
            print()
            process_choice = input("¿Desea procesar estos repositorios con el sistema avanzado? (y/N): ")
            
            if process_choice.lower() in ['y', 'yes']:
                logger.info("Iniciando procesamiento con sistema avanzado")
                print("\n🔄 Iniciando procesamiento avanzado...")
                
                # Procesar repositorios usando el sistema de collect_metrics.py
                sync_summary = await self.process_repositories_batch(
                    repositories, batch_size=5
                )
                
                # Mostrar resumen final
                print(f"\n✅ Procesamiento completado")
                print(f"Repositorios procesados: {sync_summary['total_repositories']}")
                print(f"Exitosos: {sync_summary['successful_syncs']}")
                print(f"Fallidos: {sync_summary['failed_syncs']}")
                print(f"Tasa de éxito: {sync_summary['success_rate']:.1f}%")
                print(f"Duración: {sync_summary['duration_seconds']:.1f} segundos")
                
                if sync_summary['errors']:
                    print(f"\n⚠️  Errores encontrados ({len(sync_summary['errors'])}):")
                    for error in sync_summary['errors'][:5]:  # Mostrar solo los primeros 5
                        print(f"   • {error}")
                    if len(sync_summary['errors']) > 5:
                        print(f"   ... y {len(sync_summary['errors']) - 5} errores más")
                
                return True
            else:
                print("❌ Procesamiento cancelado por el usuario")
                return False
                
        except Exception as e:
            error_msg = f"Error durante el procesamiento: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        
        finally:
            # Cerrar conexiones
            try:
                close_database()
                logger.info("Conexiones cerradas")
            except Exception as e:
                logger.error(f"Error al cerrar conexiones: {str(e)}")


async def main():
    """Función principal del script"""
    try:
        processor = RepositoryProcessor()
        success = await processor.process_all_repositories()
        
        if success:
            print("\n✅ Proceso completado exitosamente")
            print("   Los repositorios han sido procesados y guardados en la base de datos")
        else:
            print("\n❌ El proceso falló")
            print("   Revisa los errores mostrados arriba")
        
    except Exception as e:
        logger.error(f"Error en la ejecución principal: {str(e)}")
        print(f"❌ Error crítico: {str(e)}")
        sys.exit(1)
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
