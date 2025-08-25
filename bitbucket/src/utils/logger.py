"""
Sistema de logging estructurado usando Structlog
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from structlog import configure, get_logger
from structlog.stdlib import LoggerFactory
from structlog.processors import (
    TimeStamper,
    JSONRenderer,
    format_exc_info,
    add_log_level
)
from rich.console import Console
from rich.logging import RichHandler

from src.config.settings import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Configurar el sistema de logging estructurado
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_format: Formato de logging (json, console)
        log_file: Archivo de log (opcional)
    """
    settings = get_settings()
    
    # Usar configuración por defecto si no se especifica
    log_level = log_level or settings.log_level
    log_format = log_format or settings.log_format
    log_file = log_file or settings.log_file
    
    # Configurar nivel de logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Crear directorio de logs si no existe
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configurar procesadores de Structlog
    processors = [
        add_log_level,
        TimeStamper(fmt="iso"),
        format_exc_info,
    ]
    
    if log_format == "json":
        # Formato JSON para producción
        processors.append(JSONRenderer())
    else:
        # Formato console con Rich para desarrollo
        processors.append(RichHandler(
            console=Console(),
            show_time=True,
            show_path=False,
            markup=True
        ))
    
    # Configurar Structlog de manera simplificada
    configure(
        processors=processors,
        wrapper_class=LoggerFactory,
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging estándar de Python
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurar logging a archivo si se especifica
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str = __name__):
    """
    Obtener logger configurado
    
    Args:
        name: Nombre del logger (por defecto __name__)
        
    Returns:
        Logger configurado de Structlog
    """
    # Usar logging estándar de Python para evitar problemas con structlog
    import logging
    return logging.getLogger(name)


# Configurar logging al importar el módulo
setup_logging()
