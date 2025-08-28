"""
Configuración de logging para el sistema de métricas SonarCloud

Proporciona configuración centralizada de logging con soporte
para diferentes formatos y niveles de log.
"""

import logging
import logging.config
import os
import sys
from typing import Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler

from ..config.settings import get_settings


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None
) -> None:
    """
    Configurar el sistema de logging
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_format: Formato de logging (json, console)
        log_file: Archivo de log (opcional)
    """
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if log_format == "json" else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging estándar
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
            "console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(),
            },
        },
        "handlers": {
            "console": {
                "class": "rich.logging.RichHandler",
                "level": log_level,
                "formatter": "console" if log_format == "console" else "json",
                "rich_tracebacks": True,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
        },
    }
    
    # Agregar handler de archivo si se especifica
    if log_file:
        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logging_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "filename": log_file,
            "level": log_level,
            "formatter": "json" if log_format == "json" else "console",
            "encoding": "utf-8",
        }
        
        logging_config["loggers"][""]["handlers"].append("file")
    
    # Aplicar configuración
    logging.config.dictConfig(logging_config)
    
    # Configurar rich console para mejor output
    console = Console()
    
    # Log de inicio
    logger = get_logger(__name__)
    logger.info(
        "Sistema de logging configurado",
        log_level=log_level,
        log_format=log_format,
        log_file=log_file
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Obtener logger configurado
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    return structlog.get_logger(name)


# Configurar logging al importar el módulo
try:
    settings = get_settings()
    setup_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
        log_file=settings.log_file
    )
except Exception as e:
    # Fallback a configuración básica si hay error
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.error(f"Error al configurar logging: {str(e)}")
