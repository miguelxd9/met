"""
Configuración del sistema usando Pydantic Settings
"""

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuración principal del sistema de métricas DevOps
    
    Utiliza variables de entorno para configuración flexible
    """
    
    # Configuración de Bitbucket API
    bitbucket_username: str = Field(
        default="",
        env="BITBUCKET_USERNAME",
        description="Usuario de Bitbucket para autenticación"
    )
    
    bitbucket_app_password: str = Field(
        default="",
        env="BITBUCKET_APP_PASSWORD",
        description="App Password de Bitbucket para autenticación"
    )
    
    bitbucket_workspace: str = Field(
        default="",
        env="BITBUCKET_WORKSPACE",
        description="Workspace principal de Bitbucket"
    )
    
    # Configuración de Base de Datos
    database_url: str = Field(
        default="postgresql://localhost:5432/bitbucket_metrics",
        env="DATABASE_URL",
        description="URL de conexión a PostgreSQL"
    )
    
    # Configuración de API
    api_base_url: str = Field(
        default="https://api.bitbucket.org/2.0",
        env="API_BASE_URL",
        description="URL base de la API de Bitbucket"
    )
    
    api_rate_limit: int = Field(
        default=1000,
        env="API_RATE_LIMIT",
        description="Límite de requests por hora a la API"
    )
    
    api_timeout: int = Field(
        default=30,
        env="API_TIMEOUT",
        description="Timeout en segundos para requests a la API"
    )
    
    api_retry_attempts: int = Field(
        default=1,
        env="API_RETRY_ATTEMPTS",
        description="Número de intentos de reintento en caso de error"
    )
    
    # Configuración de Logging
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Nivel de logging (DEBUG, INFO, WARNING, ERROR)"
    )
    
    log_format: str = Field(
        default="json",
        env="LOG_FORMAT",
        description="Formato de logging (json, console)"
    )
    
    log_file: Optional[str] = Field(
        default=None,
        env="LOG_FILE",
        description="Archivo de log (opcional)"
    )
    
    # Configuración de Métricas
    metrics_collection_interval: int = Field(
        default=3600,
        env="METRICS_COLLECTION_INTERVAL",
        description="Intervalo en segundos para recolección de métricas"
    )
    
    batch_size: int = Field(
        default=100,
        env="BATCH_SIZE",
        description="Tamaño del lote para procesamiento de repositorios"
    )
    
    @field_validator('bitbucket_username', 'bitbucket_app_password', 'bitbucket_workspace')
    @classmethod
    def validate_bitbucket_credentials(cls, v: str) -> str:
        """Validar que las credenciales de Bitbucket estén configuradas"""
        if not v:
            raise ValueError("Las credenciales de Bitbucket deben estar configuradas")
        return v
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validar formato de URL de base de datos"""
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError("DATABASE_URL debe ser una URL válida de PostgreSQL")
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validar nivel de logging"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL debe ser uno de: {', '.join(valid_levels)}")
        return v.upper()
    
    @field_validator('api_rate_limit')
    @classmethod
    def validate_api_rate_limit(cls, v: int) -> int:
        """Validar límite de rate limiting"""
        if v <= 0:
            raise ValueError("API_RATE_LIMIT debe ser mayor a 0")
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """
    Obtener instancia de configuración
    
    Returns:
        Settings: Instancia de configuración
    """
    return settings
