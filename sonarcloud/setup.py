#!/usr/bin/env python3
"""
Script de setup para SonarCloud Metrics DevOps

Este script facilita la configuración inicial del proyecto.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Ejecutar un comando y mostrar el resultado"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado exitosamente")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}:")
        print(f"Comando: {command}")
        print(f"Error: {e.stderr}")
        return False


def check_python_version() -> bool:
    """Verificar que la versión de Python sea compatible"""
    print("🐍 Verificando versión de Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} no es compatible. Se requiere Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} es compatible")
    return True


def check_dependencies() -> bool:
    """Verificar que las dependencias estén instaladas"""
    print("\n📦 Verificando dependencias...")
    
    required_packages = [
        "sqlalchemy",
        "alembic", 
        "psycopg2",
        "httpx",
        "pydantic",
        "structlog",
        "rich"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - No instalado")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Paquetes faltantes: {', '.join(missing_packages)}")
        print("Ejecuta: pip install -r requirements.txt")
        return False
    
    return True


def check_environment_file() -> bool:
    """Verificar que el archivo .env existe"""
    print("\n🔧 Verificando archivo de configuración...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  Archivo .env no encontrado")
            print("📋 Copiando env.example a .env...")
            try:
                with open(env_example, 'r') as src:
                    with open(env_file, 'w') as dst:
                        dst.write(src.read())
                print("✅ Archivo .env creado desde env.example")
                print("⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales")
                return True
            except Exception as e:
                print(f"❌ Error al crear .env: {e}")
                return False
        else:
            print("❌ No se encontró env.example")
            return False
    else:
        print("✅ Archivo .env encontrado")
        return True


def check_database_connection() -> bool:
    """Verificar conexión a la base de datos"""
    print("\n🗄️  Verificando conexión a base de datos...")
    
    try:
        from src.config.settings import get_settings
        from src.database import test_database_connection
        
        settings = get_settings()
        print(f"📊 URL de base de datos: {settings.database_url}")
        
        if test_database_connection():
            print("✅ Conexión a base de datos exitosa")
            return True
        else:
            print("❌ No se pudo conectar a la base de datos")
            print("💡 Asegúrate de que PostgreSQL esté ejecutándose y la base de datos exista")
            return False
            
    except Exception as e:
        print(f"❌ Error al verificar base de datos: {e}")
        return False


def run_migrations() -> bool:
    """Ejecutar migraciones de Alembic"""
    print("\n🔄 Ejecutando migraciones de base de datos...")
    
    try:
        # Verificar que alembic esté configurado
        if not Path("alembic.ini").exists():
            print("❌ No se encontró alembic.ini")
            return False
        
        # Ejecutar migraciones
        result = subprocess.run(
            "alembic upgrade head", 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print("✅ Migraciones ejecutadas exitosamente")
        if result.stdout:
            print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar migraciones: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def test_sonarcloud_connection() -> bool:
    """Probar conexión a SonarCloud API"""
    print("\n☁️  Verificando conexión a SonarCloud...")
    
    try:
        from src.scripts.test_connection import test_sonarcloud_api
        from src.config.settings import get_settings
        import asyncio
        
        settings = get_settings()
        if not settings.sonarcloud_organization:
            print("⚠️  No se configuró SONARCLOUD_ORGANIZATION")
            return False
        
        # Ejecutar test de API
        result = asyncio.run(test_sonarcloud_api(settings.sonarcloud_organization))
        
        if result.get('success', False):
            print("✅ Conexión a SonarCloud exitosa")
            return True
        else:
            print(f"❌ Error en conexión a SonarCloud: {result.get('error', 'Error desconocido')}")
            return False
            
    except Exception as e:
        print(f"❌ Error al verificar SonarCloud: {e}")
        return False


def main():
    """Función principal del script de setup"""
    parser = argparse.ArgumentParser(
        description="Script de setup para SonarCloud Metrics DevOps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python setup.py                    # Verificación completa
  python setup.py --skip-db          # Saltar verificación de base de datos
  python setup.py --skip-api         # Saltar verificación de API
  python setup.py --migrations-only  # Solo ejecutar migraciones
        """
    )
    
    parser.add_argument(
        "--skip-db", 
        action="store_true", 
        help="Saltar verificación de base de datos"
    )
    parser.add_argument(
        "--skip-api", 
        action="store_true", 
        help="Saltar verificación de API de SonarCloud"
    )
    parser.add_argument(
        "--migrations-only", 
        action="store_true", 
        help="Solo ejecutar migraciones"
    )
    
    args = parser.parse_args()
    
    print("🚀 Iniciando setup de SonarCloud Metrics DevOps")
    print("=" * 50)
    
    # Si solo migraciones, ejecutar y salir
    if args.migrations_only:
        if run_migrations():
            print("\n✅ Setup completado exitosamente")
            return 0
        else:
            print("\n❌ Setup falló")
            return 1
    
    # Verificaciones básicas
    checks_passed = True
    
    if not check_python_version():
        checks_passed = False
    
    if not check_dependencies():
        checks_passed = False
    
    if not check_environment_file():
        checks_passed = False
    
    # Verificaciones opcionales
    if not args.skip_db:
        if not check_database_connection():
            checks_passed = False
        elif not run_migrations():
            checks_passed = False
    
    if not args.skip_api:
        if not test_sonarcloud_connection():
            checks_passed = False
    
    # Resumen final
    print("\n" + "=" * 50)
    if checks_passed:
        print("✅ Setup completado exitosamente")
        print("\n🎉 ¡El proyecto está listo para usar!")
        print("\n📋 Próximos pasos:")
        print("1. Edita el archivo .env con tus credenciales")
        print("2. Ejecuta: python -m src.scripts.collect_metrics --organization tu-org --sync-all")
        print("3. Revisa los logs en la carpeta logs/")
        return 0
    else:
        print("❌ Setup falló")
        print("\n🔧 Pasos para resolver problemas:")
        print("1. Verifica que PostgreSQL esté ejecutándose")
        print("2. Crea la base de datos: CREATE DATABASE sonarcloud_metrics;")
        print("3. Configura las credenciales en .env")
        print("4. Instala dependencias: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
