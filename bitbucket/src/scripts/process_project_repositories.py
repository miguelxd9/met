#!/usr/bin/env python3
"""
Script para procesar todos los repositorios de un proyecto específico

Este script lee la configuración de un proyecto desde config/project_repositories.json,
obtiene todos los repositorios del proyecto desde Bitbucket y los guarda
en la base de datos PostgreSQL.
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


class ProjectRepositoriesProcessor:
    """
    Clase para procesar todos los repositorios de un proyecto específico
    """
    
    def __init__(self):
        """Inicializar el procesador de repositorios del proyecto"""
        self.client = BitbucketClient()
        self.stats = {
            'total_processed': 0,
            'total_created': 0,
            'total_updated': 0,
            'total_errors': 0,
            'errors': []
        }
    
    async def load_project_config(self, config_file: str = "config/project_repositories.json") -> Dict[str, Any]:
        """
        Cargar configuración del proyecto desde archivo JSON
        
        Args:
            config_file: Ruta del archivo de configuración
            
        Returns:
            Configuración del proyecto
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            project_config = config.get('project', {})
            
            if not project_config:
                print(f"❌ Error: No se encontró la configuración del proyecto en: {config_file}")
                return {}
            
            print(f"📋 Configuración cargada desde: {config_file}")
            print(f"   🏢 Workspace: {project_config.get('workspace_slug')}")
            print(f"   📁 Project: {project_config.get('project_key')}")
            print()
            
            return project_config
            
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo de configuración: {config_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Error: El archivo JSON no es válido: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error al cargar configuración: {e}")
            return {}
    
    async def process_project_repositories(self, project_config: Dict[str, Any]) -> bool:
        """
        Procesar todos los repositorios del proyecto
        
        Args:
            project_config: Configuración del proyecto
            
        Returns:
            True si se procesaron exitosamente
        """
        workspace_slug = project_config.get('workspace_slug')
        project_key = project_config.get('project_key')
        
        print("🚀 Iniciando procesamiento de repositorios del proyecto...")
        print("=" * 60)
        
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
            # Obtener workspace o crearlo si no existe
            print("🏢 Procesando workspace...")
            workspace = await self._process_workspace(workspace_slug, session)
            if not workspace:
                return False
            
            # Obtener proyecto o crearlo si no existe
            print("📁 Procesando proyecto...")
            project = await self._process_project(workspace_slug, project_key, workspace.id, session)
            if not project:
                return False
            
            # Obtener todos los repositorios del proyecto desde Bitbucket
            print(f"📂 Obteniendo repositorios del proyecto: {project_key}")
            repositories_data = await self.client.get_all_project_repositories(workspace_slug, project_key)
            
            if not repositories_data:
                print("❌ No se encontraron repositorios en el proyecto")
                return False
            
            total_repositories = len(repositories_data)
            print(f"✅ Encontrados {total_repositories} repositorios para procesar")
            print()
            
            # Procesar cada repositorio
            for i, repository_data in enumerate(repositories_data, 1):
                progress = (i / total_repositories) * 100
                print(f"📋 [{i}/{total_repositories}] Procesando repositorio... ({progress:.1f}%)")
                
                success = await self._process_repository(repository_data, workspace.id, project.id, session)
                if success:
                    self.stats['total_processed'] += 1
                else:
                    self.stats['total_errors'] += 1
                
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
        else:
            # Actualizar workspace existente
            workspace.updated_at = datetime.now(timezone.utc)
            session.commit()
            print(f"      ✅ Workspace '{workspace_slug}' encontrado")
        
        return workspace
    
    async def _process_project(self, workspace_slug: str, project_key: str, workspace_id: int, session) -> Project:
        """
        Crear o actualizar project
        
        Args:
            workspace_slug: Slug del workspace
            project_key: Clave del proyecto
            workspace_id: ID del workspace
            session: Sesión de base de datos
            
        Returns:
            Instancia del proyecto
        """
        # Buscar proyecto por key
        project = session.query(Project).filter_by(key=project_key).first()
        
        if not project:
            # Obtener información del proyecto desde Bitbucket
            try:
                project_data = await self.client.get_project(workspace_slug, project_key)
                if project_data:
                    project = Project(
                        uuid=project_data.get('uuid', '').strip('{}'),
                        name=project_data.get('name', project_key),
                        key=project_key,
                        description=project_data.get('description'),
                        is_private=project_data.get('is_private', True),
                        workspace_id=workspace_id,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    session.add(project)
                    session.commit()
                    print(f"      ✅ Project '{project_key}' creado")
                else:
                    print(f"      ❌ No se pudo obtener información del proyecto: {project_key}")
                    return None
            except Exception as e:
                print(f"      ❌ Error obteniendo proyecto: {e}")
                return None
        else:
            # Actualizar proyecto existente
            project.updated_at = datetime.now(timezone.utc)
            session.commit()
            print(f"      ✅ Project '{project_key}' encontrado")
        
        return project
    
    async def _process_repository(self, repository_data: Dict[str, Any], workspace_id: int, project_id: int, session) -> bool:
        """
        Procesar un repositorio individual
        
        Args:
            repository_data: Datos del repositorio desde Bitbucket
            workspace_id: ID del workspace
            project_id: ID del proyecto
            session: Sesión de base de datos
            
        Returns:
            True si se procesó exitosamente, False en caso contrario
        """
        repo_uuid = repository_data.get('uuid', '').strip('{}')
        repo_slug = repository_data.get('slug')
        repo_name = repository_data.get('name', repo_slug)
        
        print(f"   🔍 Procesando: {repo_name}")
        print(f"      🆔 UUID: {repo_uuid}")
        print(f"      🔑 Slug: {repo_slug}")
        
        try:
            # Buscar repositorio por UUID
            repository = session.query(Repository).filter_by(uuid=repo_uuid).first()
            
            if repository:
                # Actualizar repositorio existente
                repository.name = repo_name
                repository.slug = repo_slug
                repository.description = repository_data.get('description')
                repository.language = repository_data.get('language')
                repository.size_bytes = repository_data.get('size', 0)
                repository.is_private = repository_data.get('is_private', True)
                repository.updated_at = datetime.now(timezone.utc)
                session.commit()
                print(f"      ✅ Repository '{repo_name}' actualizado")
                self.stats['total_updated'] += 1
            else:
                # Crear nuevo repositorio
                repository = Repository(
                    uuid=repo_uuid,
                    name=repo_name,
                    slug=repo_slug,
                    description=repository_data.get('description'),
                    language=repository_data.get('language'),
                    workspace_id=workspace_id,
                    project_id=project_id,
                    bitbucket_id=repository_data.get('id'),
                    size_bytes=repository_data.get('size', 0),
                    is_private=repository_data.get('is_private', True),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(repository)
                session.commit()
                print(f"      ✅ Repository '{repo_name}' creado")
                self.stats['total_created'] += 1
            
            return True
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            self.stats['errors'].append(f"Error en repositorio {repo_name}: {str(e)}")
            return False


async def main():
    """Función principal"""
    print("🚀 Procesador de Repositorios del Proyecto")
    print("=" * 60)
    print()
    
    processor = ProjectRepositoriesProcessor()
    
    # Cargar configuración del proyecto
    project_config = await processor.load_project_config()
    if not project_config:
        print("❌ No se pudo cargar la configuración del proyecto")
        sys.exit(1)
    
    success = await processor.process_project_repositories(project_config)
    
    if success:
        print("\n✅ Proceso completado exitosamente")
        print("   Los repositorios han sido guardados/actualizados en la base de datos")
    else:
        print("\n❌ El proceso falló")
        print("   Revisa los errores mostrados arriba")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
