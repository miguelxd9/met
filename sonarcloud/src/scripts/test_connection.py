"""
Script de prueba de conexión para SonarCloud

Este script permite probar las conexiones a:
- Base de datos PostgreSQL
- API de SonarCloud
- Configuración del sistema
"""

import asyncio
import argparse
import sys
from typing import Dict, Any

from ..database import init_database, close_database, test_database_connection
from ..api.sonarcloud_client import SonarCloudClient
from ..utils.logger import get_logger
from ..config.settings import get_settings


async def test_sonarcloud_api(organization_key: str) -> Dict[str, Any]:
    """
    Probar conexión a la API de SonarCloud
    
    Args:
        organization_key: Clave de la organización para probar
        
    Returns:
        Dict con resultados de las pruebas
    """
    logger = get_logger(__name__)
    results = {
        'api_connection': False,
        'organization_access': False,
        'projects_access': False,
        'error': None,
        'organization_info': None,
        'projects_count': 0
    }
    
    try:
        logger.info("Probando conexión a API de SonarCloud")
        
        # Crear cliente
        client = SonarCloudClient()
        results['api_connection'] = True
        logger.info("✅ Cliente de SonarCloud creado exitosamente")
        
        # Probar acceso a organización
        logger.info(f"Probando acceso a organización: {organization_key}")
        org_data = await client.get_organization(organization_key)
        results['organization_access'] = True
        results['organization_info'] = {
            'key': org_data.get('organization', {}).get('key'),
            'name': org_data.get('organization', {}).get('name'),
            'description': org_data.get('organization', {}).get('description')
        }
        logger.info(f"✅ Acceso a organización exitoso: {results['organization_info']['name']}")
        
        # Probar acceso a proyectos
        logger.info("Probando acceso a proyectos de la organización")
        projects = await client.get_all_organization_projects(organization_key, page=1, page_size=10)
        results['projects_access'] = True
        results['projects_count'] = len(projects)
        logger.info(f"✅ Acceso a proyectos exitoso: {len(projects)} proyectos encontrados")
        
        # Mostrar información de los primeros proyectos
        if projects:
            logger.info("📋 Primeros proyectos encontrados:")
            for i, project in enumerate(projects[:5], 1):
                logger.info(f"   {i}. {project.get('name')} ({project.get('key')})")
        
        return results
        
    except Exception as e:
        error_msg = str(e)
        results['error'] = error_msg
        logger.error(f"❌ Error en prueba de API: {error_msg}")
        return results


def test_database() -> Dict[str, Any]:
    """
    Probar conexión a la base de datos
    
    Returns:
        Dict con resultados de las pruebas
    """
    logger = get_logger(__name__)
    results = {
        'database_connection': False,
        'tables_created': False,
        'error': None
    }
    
    try:
        logger.info("Probando conexión a base de datos PostgreSQL")
        
        # Probar conexión
        if test_database_connection():
            results['database_connection'] = True
            logger.info("✅ Conexión a base de datos exitosa")
        else:
            results['error'] = "No se pudo conectar a la base de datos"
            logger.error("❌ Error de conexión a base de datos")
            return results
        
        # Inicializar base de datos y crear tablas
        logger.info("Inicializando base de datos y creando tablas")
        init_database()
        results['tables_created'] = True
        logger.info("✅ Tablas creadas exitosamente")
        
        return results
        
    except Exception as e:
        error_msg = str(e)
        results['error'] = error_msg
        logger.error(f"❌ Error en prueba de base de datos: {error_msg}")
        return results


def test_configuration() -> Dict[str, Any]:
    """
    Probar configuración del sistema
    
    Returns:
        Dict con resultados de las pruebas
    """
    logger = get_logger(__name__)
    results = {
        'config_loaded': False,
        'required_fields': {},
        'error': None
    }
    
    try:
        logger.info("Probando configuración del sistema")
        
        # Cargar configuración
        settings = get_settings()
        results['config_loaded'] = True
        logger.info("✅ Configuración cargada exitosamente")
        
        # Verificar campos requeridos
        required_fields = {
            'sonarcloud_token': bool(settings.sonarcloud_token),
            'sonarcloud_organization': bool(settings.sonarcloud_organization),
            'database_url': bool(settings.database_url),
            'api_base_url': bool(settings.api_base_url)
        }
        
        results['required_fields'] = required_fields
        
        # Verificar cada campo
        for field, is_set in required_fields.items():
            if is_set:
                logger.info(f"✅ {field}: Configurado")
            else:
                logger.warning(f"⚠️  {field}: No configurado")
        
        # Mostrar configuración (sin mostrar tokens)
        logger.info("📋 Configuración actual:")
        logger.info(f"   • Organización: {settings.sonarcloud_organization}")
        logger.info(f"   • Base de datos: {settings.database_url}")
        logger.info(f"   • API Base URL: {settings.api_base_url}")
        logger.info(f"   • Batch Size: {settings.batch_size}")
        logger.info(f"   • Log Level: {settings.log_level}")
        
        return results
        
    except Exception as e:
        error_msg = str(e)
        results['error'] = error_msg
        logger.error(f"❌ Error en prueba de configuración: {error_msg}")
        return results


def print_test_results(
    config_results: Dict[str, Any],
    db_results: Dict[str, Any],
    api_results: Dict[str, Any]
) -> None:
    """
    Imprimir resultados de las pruebas de forma legible
    
    Args:
        config_results: Resultados de prueba de configuración
        db_results: Resultados de prueba de base de datos
        api_results: Resultados de prueba de API
    """
    print("\n" + "="*80)
    print("🔧 RESULTADOS DE PRUEBAS DE CONEXIÓN SONARCLOUD")
    print("="*80)
    
    # Configuración
    print(f"\n📋 CONFIGURACIÓN:")
    if config_results['config_loaded']:
        print("   ✅ Configuración cargada exitosamente")
        
        required_fields = config_results['required_fields']
        all_fields_ok = all(required_fields.values())
        
        if all_fields_ok:
            print("   ✅ Todos los campos requeridos están configurados")
        else:
            print("   ⚠️  Algunos campos requeridos no están configurados:")
            for field, is_set in required_fields.items():
                status = "✅" if is_set else "❌"
                print(f"      {status} {field}")
    else:
        print(f"   ❌ Error al cargar configuración: {config_results.get('error', 'Desconocido')}")
    
    # Base de datos
    print(f"\n🗄️  BASE DE DATOS:")
    if db_results['database_connection']:
        print("   ✅ Conexión a PostgreSQL exitosa")
        if db_results['tables_created']:
            print("   ✅ Tablas creadas exitosamente")
        else:
            print("   ⚠️  Error al crear tablas")
    else:
        print(f"   ❌ Error de conexión: {db_results.get('error', 'Desconocido')}")
    
    # API de SonarCloud
    print(f"\n🌐 API SONARCLOUD:")
    if api_results['api_connection']:
        print("   ✅ Cliente de API creado exitosamente")
        
        if api_results['organization_access']:
            org_info = api_results['organization_info']
            print(f"   ✅ Acceso a organización: {org_info['name']} ({org_info['key']})")
            
            if api_results['projects_access']:
                print(f"   ✅ Acceso a proyectos: {api_results['projects_count']} proyectos encontrados")
            else:
                print("   ⚠️  Error al acceder a proyectos")
        else:
            print("   ❌ Error al acceder a organización")
    else:
        print(f"   ❌ Error de conexión a API: {api_results.get('error', 'Desconocido')}")
    
    # Resumen general
    print(f"\n📊 RESUMEN:")
    config_ok = config_results['config_loaded'] and all(config_results['required_fields'].values())
    db_ok = db_results['database_connection'] and db_results['tables_created']
    api_ok = api_results['api_connection'] and api_results['organization_access']
    
    total_tests = 3
    passed_tests = sum([config_ok, db_ok, api_ok])
    
    print(f"   • Configuración: {'✅' if config_ok else '❌'}")
    print(f"   • Base de datos: {'✅' if db_ok else '❌'}")
    print(f"   • API SonarCloud: {'✅' if api_ok else '❌'}")
    print(f"   • Total: {passed_tests}/{total_tests} pruebas exitosas")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ¡Todas las pruebas fueron exitosas! El sistema está listo para usar.")
    else:
        print(f"\n⚠️  Algunas pruebas fallaron. Revisa la configuración antes de continuar.")
    
    print("="*80 + "\n")


async def main():
    """
    Función principal del script
    """
    parser = argparse.ArgumentParser(
        description="Script de prueba de conexión para SonarCloud",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Probar todas las conexiones
  python -m src.scripts.test_connection --organization my-org
  
  # Probar solo configuración
  python -m src.scripts.test_connection --config-only
  
  # Probar solo base de datos
  python -m src.scripts.test_connection --db-only
  
  # Probar solo API
  python -m src.scripts.test_connection --api-only --organization my-org
        """
    )
    
    parser.add_argument(
        '--organization',
        help='Clave de la organización de SonarCloud (requerido para pruebas de API)'
    )
    
    parser.add_argument(
        '--config-only',
        action='store_true',
        help='Probar solo configuración'
    )
    
    parser.add_argument(
        '--db-only',
        action='store_true',
        help='Probar solo base de datos'
    )
    
    parser.add_argument(
        '--api-only',
        action='store_true',
        help='Probar solo API de SonarCloud'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar logs detallados'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    logger = get_logger(__name__)
    
    if args.verbose:
        # Cambiar nivel de log a DEBUG si se solicita verbose
        from ..utils.logger import setup_logging
        setup_logging(log_level="DEBUG")
    
    try:
        logger.info("Iniciando pruebas de conexión para SonarCloud")
        
        # Inicializar variables de resultados
        config_results = {'config_loaded': False, 'required_fields': {}, 'error': None}
        db_results = {'database_connection': False, 'tables_created': False, 'error': None}
        api_results = {'api_connection': False, 'organization_access': False, 'projects_access': False, 'error': None}
        
        # Ejecutar pruebas según los argumentos
        if args.config_only:
            logger.info("Ejecutando solo prueba de configuración")
            config_results = test_configuration()
            
        elif args.db_only:
            logger.info("Ejecutando solo prueba de base de datos")
            db_results = test_database()
            
        elif args.api_only:
            if not args.organization:
                logger.error("❌ Se requiere --organization para pruebas de API")
                sys.exit(1)
            logger.info("Ejecutando solo prueba de API")
            api_results = await test_sonarcloud_api(args.organization)
            
        else:
            # Ejecutar todas las pruebas
            logger.info("Ejecutando todas las pruebas")
            
            # 1. Probar configuración
            logger.info("Paso 1: Probando configuración")
            config_results = test_configuration()
            
            # 2. Probar base de datos
            logger.info("Paso 2: Probando base de datos")
            db_results = test_database()
            
            # 3. Probar API (si se proporciona organización)
            if args.organization:
                logger.info("Paso 3: Probando API de SonarCloud")
                api_results = await test_sonarcloud_api(args.organization)
            else:
                logger.warning("⚠️  No se proporcionó organización, omitiendo prueba de API")
        
        # Imprimir resultados
        print_test_results(config_results, db_results, api_results)
        
        logger.info("Pruebas de conexión completadas")
        
    except KeyboardInterrupt:
        logger.warning("Pruebas interrumpidas por el usuario")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error en ejecución de pruebas: {str(e)}")
        sys.exit(1)
        
    finally:
        # Cerrar conexiones de base de datos
        logger.info("Cerrando conexiones de base de datos")
        close_database()


if __name__ == "__main__":
    asyncio.run(main())
