"""
Script principal para recolección de métricas de SonarCloud

Este script es el punto de entrada principal para sincronizar
datos desde SonarCloud API y almacenarlos en la base de datos.
"""

import asyncio
import argparse
import sys
from typing import Optional

from ..database import init_database, close_database, get_session_context
from ..services import ProjectService, OrganizationService, MetricsService
from ..utils.logger import get_logger
from ..config.settings import get_settings


async def sync_organization_data(organization_key: str, batch_size: Optional[int] = None) -> dict:
    """
    Sincronizar datos completos de una organización
    
    Args:
        organization_key: Clave de la organización
        batch_size: Tamaño del lote para procesamiento
        
    Returns:
        Dict con estadísticas de sincronización
    """
    logger = get_logger(__name__)
    
    try:
        logger.info(f"Iniciando sincronización completa de organización: {organization_key}")
        
        # Inicializar servicios
        project_service = ProjectService()
        org_service = OrganizationService()
        metrics_service = MetricsService()
        
        # Usar context manager para manejo automático de sesiones
        with get_session_context() as session:
            # 1. Sincronizar organización
            logger.info("Paso 1: Sincronizando organización")
            org_result = await org_service.sync_organization(session, organization_key)
            logger.info(f"Organización sincronizada: {org_result['action']}")
            
            # 2. Sincronizar todos los proyectos
            logger.info("Paso 2: Sincronizando proyectos")
            projects_result = await project_service.sync_organization_projects(
                session, organization_key, batch_size
            )
            logger.info(f"Proyectos sincronizados: {projects_result}")
            
            # 3. Generar resumen de métricas
            logger.info("Paso 3: Generando resumen de métricas")
            metrics_summary = metrics_service.get_quality_metrics_summary(session, organization_key)
            logger.info(f"Resumen de métricas generado: {metrics_summary['total_projects']} proyectos")
            
            # 4. Generar resumen de proyectos
            logger.info("Paso 4: Generando resumen de proyectos")
            projects_summary = await project_service.get_projects_summary(session, organization_key)
            logger.info(f"Resumen de proyectos generado")
            
            # 5. Analizar tendencias
            logger.info("Paso 5: Analizando tendencias de calidad")
            trends = metrics_service.get_quality_trends(session, organization_key)
            logger.info(f"Tendencias analizadas: {len(trends.get('recommendations', []))} recomendaciones")
            
            # 6. Identificar proyectos que necesitan atención
            logger.info("Paso 6: Identificando proyectos que necesitan atención")
            attention_projects = metrics_service.get_projects_needing_attention(session, organization_key, limit=10)
            logger.info(f"Proyectos que necesitan atención: {len(attention_projects)}")
            
            # Compilar resultados finales
            final_results = {
                'organization_key': organization_key,
                'organization_sync': org_result,
                'projects_sync': projects_result,
                'metrics_summary': metrics_summary,
                'projects_summary': projects_summary,
                'quality_trends': trends,
                'attention_projects_count': len(attention_projects),
                'attention_projects': [
                    {
                        'key': p.key,
                        'name': p.name,
                        'quality_score': round(p.get_quality_score(), 2),
                        'reasons': getattr(p, 'attention_reasons', [])
                    }
                    for p in attention_projects
                ]
            }
            
            logger.info("Sincronización completa finalizada exitosamente")
            return final_results
            
    except Exception as e:
        logger.error(f"Error en sincronización de organización {organization_key}: {str(e)}")
        raise


async def sync_single_project(project_key: str, organization_key: str) -> dict:
    """
    Sincronizar un proyecto específico
    
    Args:
        project_key: Clave del proyecto
        organization_key: Clave de la organización
        
    Returns:
        Dict con resultado de la sincronización
    """
    logger = get_logger(__name__)
    
    try:
        logger.info(f"Sincronizando proyecto individual: {project_key}")
        
        project_service = ProjectService()
        
        with get_session_context() as session:
            result = await project_service.sync_single_project(
                session, project_key, organization_key
            )
            
            logger.info(f"Proyecto sincronizado: {result['action']}")
            return result
            
    except Exception as e:
        logger.error(f"Error al sincronizar proyecto {project_key}: {str(e)}")
        raise


async def generate_reports(organization_key: str) -> dict:
    """
    Generar reportes de métricas para una organización
    
    Args:
        organization_key: Clave de la organización
        
    Returns:
        Dict con reportes generados
    """
    logger = get_logger(__name__)
    
    try:
        logger.info(f"Generando reportes para organización: {organization_key}")
        
        project_service = ProjectService()
        metrics_service = MetricsService()
        
        with get_session_context() as session:
            # Generar diferentes tipos de reportes
            reports = {}
            
            # 1. Resumen de métricas de calidad
            reports['quality_metrics'] = metrics_service.get_quality_metrics_summary(
                session, organization_key
            )
            
            # 2. Resumen de proyectos
            reports['projects_summary'] = await project_service.get_projects_summary(
                session, organization_key
            )
            
            # 3. Tendencias de calidad
            reports['quality_trends'] = metrics_service.get_quality_trends(
                session, organization_key
            )
            
            # 4. Proyectos por prioridad (top 10)
            priority_projects = await project_service.get_projects_by_priority(
                session, organization_key, limit=10
            )
            reports['priority_projects'] = [
                {
                    'key': p.key,
                    'name': p.name,
                    'quality_score': round(p.get_quality_score(), 2),
                    'coverage': p.coverage,
                    'duplications': p.duplications,
                    'quality_gate_status': p.quality_gate_status
                }
                for p in priority_projects
            ]
            
            # 5. Proyectos que necesitan atención
            attention_projects = metrics_service.get_projects_needing_attention(
                session, organization_key, limit=10
            )
            reports['attention_projects'] = [
                {
                    'key': p.key,
                    'name': p.name,
                    'quality_score': round(p.get_quality_score(), 2),
                    'reasons': getattr(p, 'attention_reasons', [])
                }
                for p in attention_projects
            ]
            
            logger.info("Reportes generados exitosamente")
            return reports
            
    except Exception as e:
        logger.error(f"Error al generar reportes para organización {organization_key}: {str(e)}")
        raise


def print_results(results: dict) -> None:
    """
    Imprimir resultados de forma legible
    
    Args:
        results: Resultados de la sincronización
    """
    logger = get_logger(__name__)
    
    try:
        print("\n" + "="*80)
        print("📊 RESULTADOS DE SINCRONIZACIÓN SONARCLOUD")
        print("="*80)
        
        # Información de la organización
        org_key = results.get('organization_key', 'N/A')
        print(f"\n🏢 Organización: {org_key}")
        
        # Estadísticas de sincronización de proyectos
        if 'projects_sync' in results:
            projects_sync = results['projects_sync']
            print(f"\n📈 Sincronización de Proyectos:")
            print(f"   • Total de proyectos: {projects_sync.get('total_projects', 0)}")
            print(f"   • Proyectos procesados: {projects_sync.get('processed_count', 0)}")
            print(f"   • Proyectos creados: {projects_sync.get('created_count', 0)}")
            print(f"   • Proyectos actualizados: {projects_sync.get('updated_count', 0)}")
            print(f"   • Errores: {projects_sync.get('error_count', 0)}")
        
        # Resumen de métricas
        if 'metrics_summary' in results:
            metrics = results['metrics_summary']
            print(f"\n📊 Métricas de Calidad:")
            print(f"   • Cobertura promedio: {metrics.get('metrics', {}).get('coverage', {}).get('average', 0):.2f}%")
            print(f"   • Duplicación promedio: {metrics.get('metrics', {}).get('duplications', {}).get('average', 0):.2f}%")
            print(f"   • Score de calidad promedio: {metrics.get('metrics', {}).get('quality_score', {}).get('average', 0):.2f}")
            
            # Distribución de calidad
            quality_dist = metrics.get('quality_distribution', {})
            print(f"   • Distribución de calidad:")
            print(f"     - Excelente (≥90): {quality_dist.get('excellent', 0)} proyectos")
            print(f"     - Bueno (70-89): {quality_dist.get('good', 0)} proyectos")
            print(f"     - Regular (50-69): {quality_dist.get('fair', 0)} proyectos")
            print(f"     - Pobre (<50): {quality_dist.get('poor', 0)} proyectos")
        
        # Proyectos que necesitan atención
        if 'attention_projects' in results:
            attention_projects = results['attention_projects']
            if attention_projects:
                print(f"\n⚠️  Proyectos que Necesitan Atención ({len(attention_projects)}):")
                for i, project in enumerate(attention_projects[:5], 1):  # Mostrar solo los primeros 5
                    print(f"   {i}. {project['name']} ({project['key']})")
                    print(f"      Score: {project['quality_score']:.2f}")
                    if 'reasons' in project and project['reasons']:
                        print(f"      Razones: {', '.join(project['reasons'])}")
        
        # Recomendaciones
        if 'quality_trends' in results:
            trends = results['quality_trends']
            recommendations = trends.get('recommendations', [])
            if recommendations:
                print(f"\n💡 Recomendaciones:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec}")
        
        print("\n" + "="*80)
        print("✅ Sincronización completada exitosamente")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Error al imprimir resultados: {str(e)}")


async def main():
    """
    Función principal del script
    """
    parser = argparse.ArgumentParser(
        description="Script de recolección de métricas de SonarCloud",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Sincronizar organización completa
  python -m src.scripts.collect_metrics --organization my-org --sync-all
  
  # Sincronizar proyecto específico
  python -m src.scripts.collect_metrics --organization my-org --project my-project
  
  # Generar solo reportes
  python -m src.scripts.collect_metrics --organization my-org --reports-only
  
  # Especificar tamaño de lote
  python -m src.scripts.collect_metrics --organization my-org --sync-all --batch-size 50
        """
    )
    
    parser.add_argument(
        '--organization',
        required=True,
        help='Clave de la organización de SonarCloud'
    )
    
    parser.add_argument(
        '--project',
        help='Clave de un proyecto específico (opcional)'
    )
    
    parser.add_argument(
        '--sync-all',
        action='store_true',
        help='Sincronizar todos los datos de la organización'
    )
    
    parser.add_argument(
        '--reports-only',
        action='store_true',
        help='Generar solo reportes sin sincronizar datos'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        help='Tamaño del lote para procesamiento (por defecto: configuración del sistema)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar logs detallados'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    logger = get_logger(__name__)
    settings = get_settings()
    
    if args.verbose:
        # Cambiar nivel de log a DEBUG si se solicita verbose
        from ..utils.logger import setup_logging
        setup_logging(log_level="DEBUG")
    
    try:
        logger.info("Iniciando script de recolección de métricas de SonarCloud")
        logger.info(f"Organización: {args.organization}")
        logger.info(f"Configuración: sync_all={args.sync_all}, reports_only={args.reports_only}")
        
        # Inicializar base de datos
        logger.info("Inicializando base de datos")
        init_database()
        
        # Ejecutar operaciones según los argumentos
        if args.reports_only:
            # Solo generar reportes
            logger.info("Generando reportes (sin sincronización)")
            results = await generate_reports(args.organization)
            
        elif args.project:
            # Sincronizar proyecto específico
            logger.info(f"Sincronizando proyecto específico: {args.project}")
            results = await sync_single_project(args.project, args.organization)
            
        elif args.sync_all:
            # Sincronización completa
            logger.info("Iniciando sincronización completa")
            results = await sync_organization_data(args.organization, args.batch_size)
            
        else:
            # Por defecto, sincronización completa
            logger.info("Iniciando sincronización completa (por defecto)")
            results = await sync_organization_data(args.organization, args.batch_size)
        
        # Imprimir resultados
        print_results(results)
        
        logger.info("Script ejecutado exitosamente")
        
    except KeyboardInterrupt:
        logger.warning("Script interrumpido por el usuario")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error en ejecución del script: {str(e)}")
        sys.exit(1)
        
    finally:
        # Cerrar conexiones de base de datos
        logger.info("Cerrando conexiones de base de datos")
        close_database()


if __name__ == "__main__":
    asyncio.run(main())
