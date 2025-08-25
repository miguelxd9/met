#!/usr/bin/env python3
"""
Script para procesar todos los proyectos del workspace configurado

Este script obtiene todos los proyectos del workspace desde Bitbucket
y los guarda/actualiza en la base de datos PostgreSQL.
"""

import os
import sys
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
from src.config.settings import get_settings


class WorkspaceProjectsProcessor:
    """
    Clase para procesar todos los proyectos del workspace
    """
    
    def __init__(self):
        """Inicializar el procesador de proyectos del workspace"""
        self.client = BitbucketClient()
        self.settings = get_settings()
        self.stats = {
            'total_processed': 0,
            'total_created': 0,
            'total_updated': 0,
            'total_errors': 0,
            'errors': []
        }
    
    async def process_workspace_projects(self, workspace_slug: str) -> bool:
        """
        Procesar todos los proyectos del workspace
        
        Args:
            workspace_slug: Slug del workspace
            
        Returns:
            True si se procesaron exitosamente
        """
        print("🚀 Iniciando procesamiento de proyectos del workspace...")
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
            
            # Obtener todos los proyectos del workspace desde Bitbucket
            print(f"📁 Obteniendo proyectos del workspace: {workspace_slug}")
            projects_data = await self.client.get_all_workspace_projects(workspace_slug)
            
            if not projects_data:
                print("❌ No se encontraron proyectos en el workspace")
                return False
            
            total_projects = len(projects_data)
            print(f"✅ Encontrados {total_projects} proyectos para procesar")
            print()
            
            # Procesar cada proyecto
            for i, project_data in enumerate(projects_data, 1):
                progress = (i / total_projects) * 100
                print(f"📋 [{i}/{total_projects}] Procesando proyecto... ({progress:.1f}%)")
                
                success = await self._process_project(project_data, workspace.id, session)
                if success:
                    self.stats['total_processed'] += 1
                else:
                    self.stats['total_errors'] += 1
                
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
        Procesar un proyecto individual
        
        Args:
            project_data: Datos del proyecto desde Bitbucket
            workspace_id: ID del workspace
            session: Sesión de base de datos
            
        Returns:
            True si se procesó exitosamente, False en caso contrario
        """
        project_uuid = project_data.get('uuid', '').strip('{}')
        project_key = project_data.get('key')
        project_name = project_data.get('name', project_key)
        
        print(f"   🔍 Procesando: {project_name}")
        print(f"      🆔 UUID: {project_uuid}")
        print(f"      🔑 Key: {project_key}")
        
        try:
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
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            self.stats['errors'].append(f"Error en proyecto {project_name}: {str(e)}")
            return False


async def main():
    """Función principal"""
    print("🚀 Procesador de Proyectos del Workspace")
    print("=" * 60)
    print()
    
    try:
        # Obtener configuración
        settings = get_settings()
        workspace_slug = settings.bitbucket_workspace
        
        processor = WorkspaceProjectsProcessor()
        success = await processor.process_workspace_projects(workspace_slug)
        
        if success:
            print("\n✅ Proceso completado exitosamente")
            print("   Los proyectos han sido guardados/actualizados en la base de datos")
        else:
            print("\n❌ El proceso falló")
            print("   Revisa los errores mostrados arriba")
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
