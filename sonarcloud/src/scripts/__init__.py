"""
Scripts de procesamiento para SonarCloud

Proporciona scripts para:
- Recolección de métricas desde SonarCloud
- Sincronización de datos
- Generación de reportes
- Pruebas de conexión
"""

from .collect_metrics import main as collect_metrics_main
from .test_connection import main as test_connection_main

__all__ = [
    'collect_metrics_main',
    'test_connection_main'
]
