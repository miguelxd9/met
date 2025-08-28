"""
Sistema de logging estructurado usando Structlog
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from src.config.settings import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Configurar el sistema de logging
    
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
    
    # Configurar formato básico
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    
    # Configurar logging básico
    logging.basicConfig(
        level=numeric_level,
        handlers=[console_handler],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar logging a archivo si se especifica
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str = __name__):
    """
    Obtener logger configurado
    
    Args:
        name: Nombre del logger (por defecto __name__)
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


# Configurar logging al importar el módulo
setup_logging()
