#!/usr/bin/env python3
"""
Script de demostración para SonarCloud Metrics DevOps

Este script muestra las principales funcionalidades del sistema.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import get_settings
from src.api.sonarcloud_client import SonarCloudClient
from src.services import ProjectService, OrganizationService, MetricsService
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def demo_configuration():
    """Demostrar la configuración del sistema"""
    print("\n🔧 DEMOSTRACIÓN: CONFIGURACIÓN")
    print("=" * 50)
    
    try:
        settings = get_settings()
        print(f"✅ Configuración cargada exitosamente")
        print(f"   • Organización: {settings.sonarcloud_organization}")
        print(f"   • Base de datos: {settings.database_url}")
        print(f"   • API Base URL: {settings.api_base_url}")
        print(f"   • Batch Size: {settings.batch_size}")
        print(f"   • Log Level: {settings.log_level}")
        return True
    except Exception as e:
        print(f"❌ Error al cargar configuración: {e}")
        return False


async def demo_api_client():
    """Demostrar el cliente de API"""
    print("\n☁️  DEMOSTRACIÓN: CLIENTE DE API")
    print("=" * 50)
    
    try:
        client = SonarCloudClient()
        print(f"✅ Cliente de API inicializado")
        print(f"   • Rate Limiter: {client.rate_limiter.max_requests} requests/hora")
        print(f"   • Timeout: {client.settings.api_timeout} segundos")
        print(f"   • Retry attempts: {client.settings.api_retry_attempts}")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar cliente de API: {e}")
        return False


async def demo_services():
    """Demostrar los servicios"""
    print("\n🛠️  DEMOSTRACIÓN: SERVICIOS")
    print("=" * 50)
    
    try:
        project_service = ProjectService()
        org_service = OrganizationService()
        metrics_service = MetricsService()
        
        print(f"✅ Servicios inicializados")
        print(f"   • ProjectService: {type(project_service).__name__}")
        print(f"   • OrganizationService: {type(org_service).__name__}")
        print(f"   • MetricsService: {type(metrics_service).__name__}")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar servicios: {e}")
        return False


async def demo_models():
    """Demostrar los modelos de datos"""
    print("\n📊 DEMOSTRACIÓN: MODELOS DE DATOS")
    print("=" * 50)
    
    try:
        from src.models import Organization, Project, QualityGate, Metric, Issue, SecurityHotspot
        
        # Crear instancias de ejemplo
        org = Organization(
            uuid="demo-org-uuid",
            key="demo-org",
            name="Demo Organization"
        )
        
        project = Project(
            uuid="demo-project-uuid",
            key="demo-project",
            name="Demo Project",
            organization_id=1,
            coverage=85.5,
            duplications=2.1,
            maintainability_rating=1,
            reliability_rating=1,
            security_rating=1,
            bugs_count=5,
            vulnerabilities_count=2,
            code_smells_count=15,
            new_issues_count=3,
            security_hotspots_count=1,
            lines_of_code=10000,
            ncloc=8000
        )
        
        print(f"✅ Modelos creados exitosamente")
        print(f"   • Organization: {org.name} ({org.key})")
        print(f"   • Project: {project.name} ({project.key})")
        print(f"   • Coverage: {project.coverage}%")
        print(f"   • Quality Score: {project.get_quality_score():.2f}")
        return True
    except Exception as e:
        print(f"❌ Error al crear modelos: {e}")
        return False


async def demo_sorting_logic():
    """Demostrar la lógica de ordenamiento"""
    print("\n📈 DEMOSTRACIÓN: LÓGICA DE ORDENAMIENTO")
    print("=" * 50)
    
    try:
        client = SonarCloudClient()
        
        # Proyectos de ejemplo con diferentes métricas
        projects = [
            {
                "key": "project-high-coverage",
                "name": "High Coverage Project",
                "coverage": 95.0,
                "duplications": 1.5,
                "new_issues_count": 2,
                "security_hotspots": [{"vulnerability_probability": "LOW"}]
            },
            {
                "key": "project-low-coverage",
                "name": "Low Coverage Project", 
                "coverage": 45.0,
                "duplications": 8.2,
                "new_issues_count": 15,
                "security_hotspots": [{"vulnerability_probability": "HIGH"}]
            },
            {
                "key": "project-medium-coverage",
                "name": "Medium Coverage Project",
                "coverage": 75.0,
                "duplications": 3.1,
                "new_issues_count": 8,
                "security_hotspots": [{"vulnerability_probability": "MEDIUM"}]
            }
        ]
        
        # Ordenar por prioridad
        sorted_projects = client.sort_projects_by_priority(projects)
        
        print(f"✅ Proyectos ordenados por prioridad:")
        for i, project in enumerate(sorted_projects, 1):
            print(f"   {i}. {project['name']}")
            print(f"      • Coverage: {project['coverage']}%")
            print(f"      • Duplications: {project['duplications']}%")
            print(f"      • New Issues: {project['new_issues_count']}")
            print(f"      • Hotspot Risk: {project['security_hotspots'][0]['vulnerability_probability']}")
        
        return True
    except Exception as e:
        print(f"❌ Error en lógica de ordenamiento: {e}")
        return False


async def demo_rate_limiter():
    """Demostrar el rate limiter"""
    print("\n⏱️  DEMOSTRACIÓN: RATE LIMITER")
    print("=" * 50)
    
    try:
        from src.utils.rate_limiter import RateLimiter
        
        rate_limiter = RateLimiter(max_requests=5, time_window=60)
        
        print(f"✅ Rate Limiter configurado")
        print(f"   • Max requests: {rate_limiter.max_requests}")
        print(f"   • Time window: {rate_limiter.time_window} segundos")
        print(f"   • Retry attempts: {rate_limiter.retry_attempts}")
        
        # Simular algunos requests
        for i in range(3):
            await rate_limiter.execute_request(lambda: print(f"   Request {i+1} ejecutado"))
        
        stats = rate_limiter.get_stats()
        print(f"   • Requests en ventana: {stats['current_requests']}")
        print(f"   • Requests restantes: {stats['remaining_requests']}")
        
        return True
    except Exception as e:
        print(f"❌ Error en rate limiter: {e}")
        return False


async def main():
    """Función principal de demostración"""
    print("🚀 DEMOSTRACIÓN: SONARCLOUD METRICS DEVOPS")
    print("=" * 60)
    print("Este script demuestra las principales funcionalidades del sistema.")
    print("=" * 60)
    
    demos = [
        ("Configuración", demo_configuration),
        ("Cliente de API", demo_api_client),
        ("Servicios", demo_services),
        ("Modelos de Datos", demo_models),
        ("Lógica de Ordenamiento", demo_sorting_logic),
        ("Rate Limiter", demo_rate_limiter)
    ]
    
    results = []
    
    for name, demo_func in demos:
        try:
            result = await demo_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en demostración '{name}': {e}")
            results.append((name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE DEMOSTRACIONES")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} demostraciones exitosas")
    
    if passed == total:
        print("🎉 ¡Todas las demostraciones fueron exitosas!")
        print("✅ El sistema está funcionando correctamente")
    else:
        print("⚠️  Algunas demostraciones fallaron")
        print("🔧 Revisa la configuración y dependencias")
    
    print("\n📋 Próximos pasos:")
    print("1. Configura las credenciales en .env")
    print("2. Crea la base de datos PostgreSQL")
    print("3. Ejecuta las migraciones: python -m alembic upgrade head")
    print("4. Prueba la conexión: python -m src.scripts.test_connection --organization tu-org")
    print("5. Recolecta métricas: python -m src.scripts.collect_metrics --organization tu-org --sync-all")


if __name__ == "__main__":
    asyncio.run(main())
