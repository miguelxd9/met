#!/usr/bin/env python3
"""
Script para crear todas las tablas de la base de datos

Este script inicializa la base de datos PostgreSQL creando todas las tablas
necesarias para el sistema de métricas DevOps de Bitbucket.

Uso:
    python create_tables.py

Requisitos:
    - PostgreSQL instalado y corriendo
    - Base de datos 'metricas_devops' creada
    - Variables de entorno configuradas (DATABASE_URL)
"""

import os
import sys
from datetime import datetime

# Agregar el directorio raíz del proyecto al path de Python
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.database.connection import init_database, engine
from src.models.base import Base
from src.models.workspace import Workspace
from src.models.project import Project
from src.models.repository import Repository
from src.models.commit import Commit
from src.models.pull_request import PullRequest


def create_all_tables():
    """Crear todas las tablas de la base de datos"""
    print("🗄️  Iniciando creación de tablas de la base de datos...")
    print("=" * 60)
    
    try:
        # Inicializar conexión a la base de datos
        print("🔌 Inicializando conexión a la base de datos...")
        init_database()
        print("✅ Conexión inicializada")
        
        # Crear todas las tablas
        print("📋 Creando tablas...")
        Base.metadata.create_all(bind=engine)
        print("✅ Todas las tablas creadas exitosamente")
        
        # Verificar que se crearon correctamente
        print("🔍 Verificando tablas creadas...")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📊 Total de tablas creadas: {len(tables)}")
        for i, table in enumerate(tables, 1):
            print(f"   {i}. {table}")
        
        # Mostrar estructura de cada tabla
        print("\n📋 Estructura de las tablas:")
        print("-" * 40)
        
        for table_name in tables:
            print(f"\n🏷️  Tabla: {table_name}")
            columns = inspector.get_columns(table_name)
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"   • {col['name']}: {col['type']} ({nullable})")
        
        print("\n🎉 ¡Base de datos inicializada exitosamente!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        print("\n🔧 Solución de problemas:")
        print("   1. Verifica que PostgreSQL esté corriendo")
        print("   2. Confirma que la base de datos 'metricas_devops' existe")
        print("   3. Verifica las credenciales en DATABASE_URL")
        print("   4. Asegúrate de que el usuario tenga permisos")
        return False


def verify_connection():
    """Verificar conexión a la base de datos"""
    print("🔍 Verificando conexión a la base de datos...")
    
    try:
        from src.database.connection import get_database_session
        session = get_database_session()
        session.execute("SELECT 1")
        session.close()
        print("✅ Conexión a la base de datos exitosa")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


def check_database_exists():
    """Verificar si la base de datos existe"""
    print("🔍 Verificando existencia de la base de datos...")
    
    try:
        # Intentar conectar a la base de datos específica
        from src.database.connection import get_database_session
        session = get_database_session()
        session.execute("SELECT current_database()")
        db_name = session.execute("SELECT current_database()").scalar()
        session.close()
        print(f"✅ Conectado a la base de datos: {db_name}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Para crear la base de datos:")
        print("   psql -U postgres -c 'CREATE DATABASE metricas_devops;'")
        return False


def main():
    """Función principal"""
    print("🚀 Script de Creación de Tablas - Métricas DevOps")
    print("=" * 60)
    print()
    
    # Verificar conexión
    if not verify_connection():
        print("❌ No se pudo conectar a la base de datos")
        sys.exit(1)
    
    # Verificar que la base de datos existe
    if not check_database_exists():
        print("❌ La base de datos no existe o no se puede acceder")
        sys.exit(1)
    
    # Crear tablas
    success = create_all_tables()
    
    if success:
        print("\n✅ Proceso completado exitosamente")
        print("   Las tablas están listas para usar")
        print("\n📝 Próximos pasos:")
        print("   1. Configurar variables de entorno (.env)")
        print("   2. Ejecutar: python src/scripts/test_connection.py")
        print("   3. Ejecutar: python src/scripts/process_workspace_projects.py")
    else:
        print("\n❌ El proceso falló")
        print("   Revisa los errores mostrados arriba")
        sys.exit(1)


if __name__ == "__main__":
    main()
