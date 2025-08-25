#!/usr/bin/env python3
"""
Script para procesar proyectos específicos configurados en JSON

Este script lee la configuración de proyectos desde config/projects.json,
obtiene información detallada de cada uno desde Bitbucket y los guarda
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
from src.models.project import Project
from src.models.workspace import Workspace
from src.api.bitbucket_client import BitbucketClient


class ConfigProjectsProcessor:
    """
    Clase para procesar proyectos configurados en JSON
    """
    
    def __init__(self):
        """Inicializar el procesador de proyectos configurados"""
        self.client = BitbucketClient()
        self.stats = {
            'total_processed': 0,
            'total_created': 0,
            'total_updated': 0,
            'total_errors': 0,
            'errors': []
        }
    
    async def load_projects_config(self, config_file: str = "config/projects.json") -> List[Dict[str, Any]]:
        """
        Cargar configuración de proyectos desde archivo JSON
        
        Args:
            config_file: Ruta del archivo de configuración
            
        Returns:
            Lista de proyectos a procesar
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            projects = config.get('projects', [])
            
            print(f"📋 Configuración cargada desde: {config_file}")
            print(f"   📊 Total de proyectos: {len(projects)}")
            print()
            
            return projects
            
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo de configuración: {config_file}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error: El archivo JSON no es válido: {e}")
            return []
        except Exception as e:
            print(f"❌ Error al cargar configuración: {e}")
            return []
    
    async def process_project(self, project_config: Dict[str, Any], session) -> bool:
        """
        Procesar un proyecto individual
        
        Args:
            project_config: Configuración del proyecto
            session: Sesión de base de datos
            
        Returns:
            True si se procesó exitosamente, False en caso contrario
        """
        workspace_slug = project_config.get('workspace_slug')
        project_key = project_config.get('project_key')
        
        print(f"🔍 Procesando: {project_key}")
        print(f"   🏢 Workspace: {workspace_slug}")
        
        try:
            # Obtener información del proyecto desde Bitbucket
            print("   📡 Obteniendo datos desde Bitbucket...")
            project_data = await self.client.get_project(workspace_slug, project_key)
            
            if not project_data:
                print("   ❌ No se pudo obtener información del proyecto")
                self.stats['total_errors'] += 1
                self.stats['errors'].append(f"Error obteniendo {project_key}")
                return False
            
            print("   ✅ Datos obtenidos de Bitbucket")
            
            # Extraer datos del proyecto
            project_uuid = project_data.get('uuid')
            project_name = project_data.get('name', project_key)
            
            # Paso 1: Crear o actualizar Workspace
            print("   🏢 Procesando Workspace...")
            workspace = await self._process_workspace(workspace_slug, session)
            if not workspace:
                return False
            
            # Paso 2: Crear o actualizar Project
            print("   📁 Procesando Project...")
            project_updated = await self._process_project(project_data, workspace.id, session)
            
            if project_updated:
                print("   ✅ Proyecto procesado exitosamente")
                self.stats['total_processed'] += 1
                return True
            else:
                print("   ❌ Error al procesar proyecto")
                self.stats['total_errors'] += 1
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.stats['total_errors'] += 1
            self.stats['errors'].append(f"Error en {project_key}: {str(e)}")
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
        else:
            # Actualizar workspace existente
            workspace.updated_at = datetime.now(timezone.utc)
            session.commit()
            print(f"      ✅ Workspace '{workspace_slug}' encontrado")
        
        return workspace
    
    async def _process_project(self, project_data: Dict[str, Any], workspace_id: int, session) -> bool:
        """
        Crear o actualizar project
        
        Args:
            project_data: Datos del proyecto desde Bitbucket
            workspace_id: ID del workspace
            session: Sesión de base de datos
            
        Returns:
            True si se procesó exitosamente
        """
        project_uuid = project_data.get('uuid')
        project_key = project_data.get('key')
        project_name = project_data.get('name', project_key)
        
        # Buscar proyecto por UUID
        project = session.query(Project).filter_by(uuid=project_uuid).first()
        
        if project:
            # Actualizar proyecto existente
            project.name = project_name
            project.key = project_key
            project.description = project_data.get('description')
            project.is_private = project_data.get('is_private', True)
            project.updated_at = datetime.now(timezone.utc)
            session.commit()
            print(f"      ✅ Project '{project_name}' actualizado")
            self.stats['total_updated'] += 1
        else:
            # Crear nuevo proyecto
            project = Project(
                uuid=project_uuid,
                name=project_name,
                key=project_key,
                description=project_data.get('description'),
                is_private=project_data.get('is_private', True),
                workspace_id=workspace_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(project)
            session.commit()
            print(f"      ✅ Project '{project_name}' creado")
            self.stats['total_created'] += 1
        
        return True
    
    async def process_all_projects(self, config_file: str = "config/projects.json") -> bool:
        """
        Procesar todos los proyectos configurados
        
        Args:
            config_file: Ruta del archivo de configuración
            
        Returns:
            True si se procesaron exitosamente
        """
        print("🚀 Iniciando procesamiento de proyectos configurados...")
        print("=" * 60)
        
        # Cargar configuración
        projects = await self.load_projects_config(config_file)
        if not projects:
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
            # Procesar cada proyecto
            for i, project_config in enumerate(projects, 1):
                progress = (i / len(projects)) * 100
                print(f"📋 [{i}/{len(projects)}] Procesando proyecto... ({progress:.1f}%)")
                await self.process_project(project_config, session)
                print()  # Línea en blanco para separar proyectos
            
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
    print("🚀 Procesador de Proyectos Configurados")
    print("=" * 60)
    print()
    
    processor = ConfigProjectsProcessor()
    success = await processor.process_all_projects()
    
    if success:
        print("\n✅ Proceso completado exitosamente")
        print("   Los proyectos han sido guardados/actualizados en la base de datos")
    else:
        print("\n❌ El proceso falló")
        print("   Revisa los errores mostrados arriba")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
