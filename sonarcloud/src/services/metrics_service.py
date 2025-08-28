"""
Servicio de métricas para SonarCloud

Proporciona lógica de negocio para el procesamiento y análisis
de métricas de calidad de código de SonarCloud.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..database.repositories import ProjectRepository, MetricRepository
from ..models import Project
from ..utils.logger import get_logger
from ..config.settings import get_settings


class MetricsService:
    """
    Servicio para análisis de métricas de SonarCloud
    
    Maneja la lógica de negocio para calcular, analizar y reportar
    métricas de calidad de código.
    """
    
    def __init__(self):
        """Inicializar servicio de métricas"""
        self.project_repo = ProjectRepository()
        self.metric_repo = MetricRepository()
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        self.logger.info("Servicio de métricas inicializado")
    
    def get_quality_metrics_summary(
        self,
        session: Session,
        organization_key: str
    ) -> Dict[str, Any]:
        """
        Obtener resumen de métricas de calidad
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            
        Returns:
            Dict con resumen de métricas de calidad
        """
        try:
            self.logger.info(f"Generando resumen de métricas de calidad - Organization: {organization_key}")
            
            # Obtener proyectos de la organización
            projects = self.project_repo.get_by_organization_key(session, organization_key)
            
            if not projects:
                return {
                    'organization_key': organization_key,
                    'total_projects': 0,
                    'metrics': {},
                    'quality_distribution': {},
                    'threshold_analysis': {}
                }
            
            # Calcular métricas agregadas
            total_projects = len(projects)
            
            # Métricas de cobertura
            coverage_data = [p.coverage for p in projects if p.coverage is not None]
            avg_coverage = sum(coverage_data) / len(coverage_data) if coverage_data else 0
            min_coverage = min(coverage_data) if coverage_data else 0
            max_coverage = max(coverage_data) if coverage_data else 0
            
            # Métricas de duplicación
            duplication_data = [p.duplications for p in projects if p.duplications is not None]
            avg_duplications = sum(duplication_data) / len(duplication_data) if duplication_data else 0
            min_duplications = min(duplication_data) if duplication_data else 0
            max_duplications = max(duplication_data) if duplication_data else 0
            
            # Métricas de issues
            total_bugs = sum(p.bugs_count for p in projects)
            total_vulnerabilities = sum(p.vulnerabilities_count for p in projects)
            total_code_smells = sum(p.code_smells_count for p in projects)
            total_new_issues = sum(p.new_issues_count for p in projects)
            
            # Métricas de security hotspots
            total_security_hotspots = sum(p.security_hotspots_count for p in projects)
            total_reviewed_hotspots = sum(p.security_hotspots_reviewed_count for p in projects)
            
            # Quality scores
            quality_scores = [p.get_quality_score() for p in projects]
            avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            min_quality_score = min(quality_scores) if quality_scores else 0
            max_quality_score = max(quality_scores) if quality_scores else 0
            
            # Distribución de calidad
            quality_distribution = {
                'excellent': len([s for s in quality_scores if s >= 90]),
                'good': len([s for s in quality_scores if 70 <= s < 90]),
                'fair': len([s for s in quality_scores if 50 <= s < 70]),
                'poor': len([s for s in quality_scores if s < 50])
            }
            
            # Análisis de umbrales
            threshold_analysis = {
                'coverage_below_threshold': len([p for p in projects if p.coverage < self.settings.coverage_threshold]),
                'duplications_above_threshold': len([p for p in projects if p.duplications > self.settings.duplication_threshold]),
                'quality_gate_failed': len([p for p in projects if p.quality_gate_status == 'FAILED']),
                'high_issue_projects': len([p for p in projects if (p.bugs_count + p.vulnerabilities_count + p.code_smells_count) > 100])
            }
            
            summary = {
                'organization_key': organization_key,
                'total_projects': total_projects,
                'metrics': {
                    'coverage': {
                        'average': round(avg_coverage, 2),
                        'minimum': round(min_coverage, 2),
                        'maximum': round(max_coverage, 2)
                    },
                    'duplications': {
                        'average': round(avg_duplications, 2),
                        'minimum': round(min_duplications, 2),
                        'maximum': round(max_duplications, 2)
                    },
                    'issues': {
                        'total_bugs': total_bugs,
                        'total_vulnerabilities': total_vulnerabilities,
                        'total_code_smells': total_code_smells,
                        'total_new_issues': total_new_issues,
                        'average_issues_per_project': round((total_bugs + total_vulnerabilities + total_code_smells) / total_projects, 2)
                    },
                    'security_hotspots': {
                        'total': total_security_hotspots,
                        'reviewed': total_reviewed_hotspots,
                        'review_rate': round((total_reviewed_hotspots / total_security_hotspots * 100) if total_security_hotspots > 0 else 0, 2)
                    },
                    'quality_score': {
                        'average': round(avg_quality_score, 2),
                        'minimum': round(min_quality_score, 2),
                        'maximum': round(max_quality_score, 2)
                    }
                },
                'quality_distribution': quality_distribution,
                'threshold_analysis': threshold_analysis
            }
            
            self.logger.info(f"Resumen de métricas generado - Organization: {organization_key}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error al generar resumen de métricas: {str(e)}")
            raise
    
    def get_projects_by_quality_range(
        self,
        session: Session,
        organization_key: str,
        min_score: float = 0.0,
        max_score: float = 100.0,
        limit: Optional[int] = None
    ) -> List[Project]:
        """
        Obtener proyectos por rango de calidad
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            min_score: Score mínimo de calidad
            max_score: Score máximo de calidad
            limit: Límite de resultados
            
        Returns:
            Lista de proyectos en el rango especificado
        """
        try:
            self.logger.info(f"Obteniendo proyectos por rango de calidad - Organization: {organization_key}, Range: {min_score}-{max_score}")
            
            projects = self.project_repo.get_projects_by_quality_score(
                session, min_score, max_score, limit
            )
            
            self.logger.info(f"Proyectos obtenidos por rango de calidad - Total: {len(projects)}")
            return projects
            
        except Exception as e:
            self.logger.error(f"Error al obtener proyectos por rango de calidad: {str(e)}")
            raise
    
    def get_projects_needing_attention(
        self,
        session: Session,
        organization_key: str,
        limit: Optional[int] = None
    ) -> List[Project]:
        """
        Obtener proyectos que necesitan atención
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            limit: Límite de resultados
            
        Returns:
            Lista de proyectos que necesitan atención
        """
        try:
            self.logger.info(f"Identificando proyectos que necesitan atención - Organization: {organization_key}")
            
            # Obtener proyectos de la organización
            projects = self.project_repo.get_by_organization_key(session, organization_key)
            
            # Filtrar proyectos que necesitan atención
            attention_projects = []
            
            for project in projects:
                needs_attention = False
                reasons = []
                
                # Verificar cobertura baja
                if project.coverage < self.settings.coverage_threshold:
                    needs_attention = True
                    reasons.append(f"Baja cobertura ({project.coverage}%)")
                
                # Verificar duplicación alta
                if project.duplications > self.settings.duplication_threshold:
                    needs_attention = True
                    reasons.append(f"Alta duplicación ({project.duplications}%)")
                
                # Verificar quality gate fallido
                if project.quality_gate_status == 'FAILED':
                    needs_attention = True
                    reasons.append("Quality gate fallido")
                
                # Verificar muchos issues
                total_issues = project.bugs_count + project.vulnerabilities_count + project.code_smells_count
                if total_issues > 100:
                    needs_attention = True
                    reasons.append(f"Muchos issues ({total_issues})")
                
                # Verificar security hotspots sin revisar
                if project.security_hotspots_count > 0:
                    review_rate = (project.security_hotspots_reviewed_count / project.security_hotspots_count * 100) if project.security_hotspots_count > 0 else 0
                    if review_rate < 50:
                        needs_attention = True
                        reasons.append(f"Baja tasa de revisión de hotspots ({review_rate:.1f}%)")
                
                if needs_attention:
                    project.attention_reasons = reasons
                    attention_projects.append(project)
            
            # Ordenar por score de calidad (peor primero)
            attention_projects.sort(key=lambda p: p.get_quality_score())
            
            if limit:
                attention_projects = attention_projects[:limit]
            
            self.logger.info(f"Proyectos que necesitan atención identificados - Total: {len(attention_projects)}")
            return attention_projects
            
        except Exception as e:
            self.logger.error(f"Error al identificar proyectos que necesitan atención: {str(e)}")
            raise
    
    def get_quality_trends(
        self,
        session: Session,
        organization_key: str
    ) -> Dict[str, Any]:
        """
        Obtener tendencias de calidad
        
        Args:
            session: Sesión de base de datos
            organization_key: Clave de la organización
            
        Returns:
            Dict con tendencias de calidad
        """
        try:
            self.logger.info(f"Analizando tendencias de calidad - Organization: {organization_key}")
            
            # Obtener proyectos de la organización
            projects = self.project_repo.get_by_organization_key(session, organization_key)
            
            if not projects:
                return {
                    'organization_key': organization_key,
                    'trends': {},
                    'recommendations': []
                }
            
            # Calcular métricas para tendencias
            quality_scores = [p.get_quality_score() for p in projects]
            coverage_scores = [p.coverage for p in projects if p.coverage is not None]
            duplication_scores = [p.duplications for p in projects if p.duplications is not None]
            
            # Análisis de tendencias
            trends = {
                'quality_score': {
                    'average': round(sum(quality_scores) / len(quality_scores), 2),
                    'distribution': {
                        'excellent': len([s for s in quality_scores if s >= 90]),
                        'good': len([s for s in quality_scores if 70 <= s < 90]),
                        'fair': len([s for s in quality_scores if 50 <= s < 70]),
                        'poor': len([s for s in quality_scores if s < 50])
                    }
                },
                'coverage': {
                    'average': round(sum(coverage_scores) / len(coverage_scores), 2) if coverage_scores else 0,
                    'projects_below_threshold': len([p for p in projects if p.coverage < self.settings.coverage_threshold])
                },
                'duplications': {
                    'average': round(sum(duplication_scores) / len(duplication_scores), 2) if duplication_scores else 0,
                    'projects_above_threshold': len([p for p in projects if p.duplications > self.settings.duplication_threshold])
                },
                'quality_gates': {
                    'passed': len([p for p in projects if p.quality_gate_status == 'PASSED']),
                    'failed': len([p for p in projects if p.quality_gate_status == 'FAILED']),
                    'pass_rate': round(len([p for p in projects if p.quality_gate_status == 'PASSED']) / len(projects) * 100, 2)
                }
            }
            
            # Generar recomendaciones
            recommendations = []
            
            if trends['coverage']['projects_below_threshold'] > len(projects) * 0.3:
                recommendations.append("Más del 30% de proyectos tienen cobertura baja. Considerar implementar mejores prácticas de testing.")
            
            if trends['duplications']['projects_above_threshold'] > len(projects) * 0.2:
                recommendations.append("Más del 20% de proyectos tienen alta duplicación. Revisar y refactorizar código duplicado.")
            
            if trends['quality_gates']['pass_rate'] < 80:
                recommendations.append("Tasa de aprobación de quality gates menor al 80%. Revisar y ajustar criterios de calidad.")
            
            avg_quality = trends['quality_score']['average']
            if avg_quality < 70:
                recommendations.append(f"Score de calidad promedio bajo ({avg_quality}). Implementar mejoras en procesos de desarrollo.")
            
            trends_data = {
                'organization_key': organization_key,
                'trends': trends,
                'recommendations': recommendations
            }
            
            self.logger.info(f"Tendencias de calidad analizadas - Organization: {organization_key}")
            return trends_data
            
        except Exception as e:
            self.logger.error(f"Error al analizar tendencias de calidad: {str(e)}")
            raise
