#!/usr/bin/env python3
"""
Script principal para procesar y guardar repositorios en la base de datos

Este script lee la configuración de repositorios desde config/repositories.json,
obtiene información detallada de cada uno desde Bitbucket y los guarda
en la base de datos PostgreSQL. Si un repositorio ya existe, solo actualiza
sus datos.
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any

# Agregar el directorio raíz del proyecto al path de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.database.connection import init_database, get_database_session
from src.models.repository import Repository
from src.models.project import Project
from src.models.workspace import Workspace
from src.api.bitbucket_client import BitbucketClient


class RepositoryProcessor:
    """
    Clase para procesar y guardar repositorios en la base de datos
    """
    
    def __init__(self):
        """Inicializar el procesador de repositorios"""
        self.client = BitbucketClient()
        self.stats = {
            'total_processed': 0,
            'total_created': 0,
            'total_updated': 0,
            'total_errors': 0,
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
            
            print(f"📋 Configuración cargada desde: {config_file}")
            print(f"   📊 Total de repositorios: {len(repositories)}")
            print()
            
            return repositories
            
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo de configuración: {config_file}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error: El archivo JSON no es válido: {e}")
            return []
        except Exception as e:
            print(f"❌ Error al cargar configuración: {e}")
            return []
    
    async def process_repository(self, repo_config: Dict[str, Any], session) -> bool:
        """
        Procesar un repositorio individual
        
        Args:
            repo_config: Configuración del repositorio
            session: Sesión de base de datos
            
        Returns:
            True si se procesó exitosamente, False en caso contrario
        """
        workspace_slug = repo_config.get('workspace_slug')
        repository_slug = repo_config.get('repository_slug')
        
        print(f"🔍 Procesando: {repository_slug}")
        print(f"   🏢 Workspace: {workspace_slug}")
        
        try:
            # Obtener información del repositorio desde Bitbucket
            print("   📡 Obteniendo datos desde Bitbucket...")
            repository_data = await self.client.get_repository(workspace_slug, repository_slug)
            
            if not repository_data:
                print("   ❌ No se pudo obtener información del repositorio")
                self.stats['total_errors'] += 1
                self.stats['errors'].append(f"Error obteniendo {repository_slug}")
                return False
            
            print("   ✅ Datos obtenidos de Bitbucket")
            
            # Extraer datos del repositorio
            repo_name = repository_data.get('name', repository_slug)
            project_data = repository_data.get('project', {})
            project_key = project_data.get('key', 'UNKNOWN')
            project_name = project_data.get('name', 'Proyecto Desconocido')
            
            # Paso 1: Crear o actualizar Workspace
            print("   🏢 Procesando Workspace...")
            workspace = await self._process_workspace(workspace_slug, session)
            if not workspace:
                return False
            
            # Paso 2: Crear o actualizar Project
            print("   📁 Procesando Project...")
            project = await self._process_project(project_key, project_name, workspace.id, session)
            if not project:
                return False
            
            # Paso 3: Crear o actualizar Repository
            print("   📂 Procesando Repository...")
            repository_updated = await self._process_repository(
                repository_data, workspace.id, project.id, session
            )
            
            if repository_updated:
                print("   ✅ Repositorio procesado exitosamente")
                self.stats['total_processed'] += 1
                return True
            else:
                print("   ❌ Error al procesar repositorio")
                self.stats['total_errors'] += 1
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.stats['total_errors'] += 1
            self.stats['errors'].append(f"Error en {repository_slug}: {str(e)}")
            return False
    
    async def _process_workspace(self, workspace_slug: str, session) -> Workspace:
        """
        Crear o actualizar workspace
        
        Args:
            workspace_slug: Slug del workspace
            session: Sesión de base de datos
            
        Returns:
            Instancia del workspace
        """
        workspace = session.query(Workspace).filter_by(slug=workspace_slug).first()
        
        if not workspace:
            # Crear nuevo workspace
            import uuid
            workspace_uuid = str(uuid.uuid4())
            workspace = Workspace(
                uuid=workspace_uuid,
                slug=workspace_slug,
                name=workspace_slug.title(),
                bitbucket_id=workspace_slug,
                is_private=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(workspace)
            session.commit()
            print(f"      ✅ Workspace '{workspace_slug}' creado")
            self.stats['total_created'] += 1
        else:
            # Actualizar workspace existente
            workspace.updated_at = datetime.now(timezone.utc)
            session.commit()
            print(f"      ✅ Workspace '{workspace_slug}' encontrado")
        
        return workspace
    
    async def _process_project(self, project_key: str, project_name: str, workspace_id: int, session) -> Project:
        """
        Crear o actualizar project
        
        Args:
            project_key: Clave del proyecto
            project_name: Nombre del proyecto
            workspace_id: ID del workspace
            session: Sesión de base de datos
            
        Returns:
            Instancia del project
        """
        project = session.query(Project).filter_by(key=project_key).first()
        
        if not project:
            # Crear nuevo project
            import uuid
            project_uuid = str(uuid.uuid4())
            project = Project(
                uuid=project_uuid,
                key=project_key,
                name=project_name,
                workspace_id=workspace_id,
                bitbucket_id=project_key,
                is_private=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(project)
            session.commit()
            print(f"      ✅ Project '{project_key}' creado")
            self.stats['total_created'] += 1
        else:
            # Actualizar project existente
            project.name = project_name
            project.updated_at = datetime.now(timezone.utc)
            session.commit()
            print(f"      ✅ Project '{project_key}' encontrado")
        
        return project
    
    async def _process_repository(self, repository_data: Dict[str, Any], workspace_id: int, project_id: int, session) -> bool:
        """
        Crear o actualizar repository
        
        Args:
            repository_data: Datos del repositorio desde Bitbucket
            workspace_id: ID del workspace
            project_id: ID del project
            session: Sesión de base de datos
            
        Returns:
            True si se procesó exitosamente
        """
        repo_slug = repository_data.get('slug')
        repo_name = repository_data.get('name', repo_slug)
        
        # Buscar repositorio existente por slug (identidad única)
        existing_repo = session.query(Repository).filter_by(slug=repo_slug).first()
        
        if existing_repo:
            # Actualizar repositorio existente
            existing_repo.name = repo_name
            existing_repo.workspace_id = workspace_id
            existing_repo.project_id = project_id
            existing_repo.size_bytes = repository_data.get('size', 0)
            existing_repo.last_activity_date = datetime.now(timezone.utc)
            existing_repo.updated_at = datetime.now(timezone.utc)
            
            # Actualizar campos adicionales si están disponibles
            if 'description' in repository_data:
                existing_repo.description = repository_data.get('description')
            if 'language' in repository_data:
                existing_repo.language = repository_data.get('language')
            if 'is_private' in repository_data:
                existing_repo.is_private = repository_data.get('is_private', True)
            
            session.commit()
            print(f"      ✅ Repository '{repo_slug}' actualizado")
            self.stats['total_updated'] += 1
        else:
            # Crear nuevo repositorio
            import uuid
            repo_uuid = str(uuid.uuid4())
            new_repo = Repository(
                uuid=repo_uuid,
                name=repo_name,
                slug=repo_slug,
                workspace_id=workspace_id,
                project_id=project_id,
                bitbucket_id=repo_slug,
                size_bytes=repository_data.get('size', 0),
                is_private=repository_data.get('is_private', True),
                description=repository_data.get('description'),
                language=repository_data.get('language'),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(new_repo)
            session.commit()
            print(f"      ✅ Repository '{repo_slug}' creado")
            self.stats['total_created'] += 1
        
        return True
    
    async def process_all_repositories(self, config_file: str = "config/repositories.json") -> bool:
        """
        Procesar todos los repositorios configurados
        
        Args:
            config_file: Ruta del archivo de configuración
            
        Returns:
            True si se procesaron exitosamente
        """
        print("🚀 Iniciando procesamiento de repositorios...")
        print("=" * 60)
        
        # Cargar configuración
        repositories = await self.load_repositories_config(config_file)
        if not repositories:
            return False
        
        # Inicializar base de datos
        print("🗄️  Inicializando base de datos...")
        init_database()
        print("✅ Base de datos inicializada")
        
        # Obtener sesión de base de datos
        print("🔌 Obteniendo sesión de base de datos...")
        session = get_database_session()
        print("✅ Sesión obtenida")
        print()
        
        try:
            # Procesar cada repositorio
            for i, repo_config in enumerate(repositories, 1):
                print(f"📋 [{i}/{len(repositories)}] Procesando repositorio...")
                await self.process_repository(repo_config, session)
                print()  # Línea en blanco para separar repositorios
            
            # Mostrar resumen final
            print("🎯 RESUMEN DEL PROCESAMIENTO")
            print("=" * 40)
            print(f"📊 Total procesados: {self.stats['total_processed']}")
            print(f"🆕 Total creados: {self.stats['total_created']}")
            print(f"🔄 Total actualizados: {self.stats['total_updated']}")
            print(f"❌ Total errores: {self.stats['total_errors']}")
            
            if self.stats['errors']:
                print("\n⚠️  Errores encontrados:")
                for error in self.stats['errors']:
                    print(f"   • {error}")
            
            print("\n🎉 ¡Procesamiento completado!")
            return True
            
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {e}")
            session.rollback()
            return False
        finally:
            session.close()
            print("🔌 Sesión de base de datos cerrada")


async def main():
    """Función principal"""
    print("🚀 Procesador de Repositorios de Bitbucket")
    print("=" * 60)
    print()
    
    processor = RepositoryProcessor()
    success = await processor.process_all_repositories()
    
    if success:
        print("\n✅ Proceso completado exitosamente")
        print("   Los repositorios han sido guardados/actualizados en la base de datos")
    else:
        print("\n❌ El proceso falló")
        print("   Revisa los errores mostrados arriba")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
