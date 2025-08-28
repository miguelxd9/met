"""
Configuración del sistema usando Pydantic Settings
"""

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuración principal del sistema de métricas DevOps para SonarCloud
    
    Utiliza variables de entorno para configuración flexible
    """
    
    # Configuración de SonarCloud API
    sonarcloud_token: str = Field(
        default="",
        env="SONARCLOUD_TOKEN",
        description="Token de autenticación de SonarCloud"
    )
    
    sonarcloud_organization: str = Field(
        default="",
        env="SONARCLOUD_ORGANIZATION",
        description="Organización principal de SonarCloud"
    )
    
    # Configuración de Base de Datos
    database_url: str = Field(
        default="postgresql://localhost:5432/sonarcloud_metrics",
        env="DATABASE_URL",
        description="URL de conexión a PostgreSQL"
    )
    
    # Configuración de API
    api_base_url: str = Field(
        default="https://sonarcloud.io/api",
        env="API_BASE_URL",
        description="URL base de la API de SonarCloud"
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
        description="Tamaño del lote para procesamiento de proyectos"
    )
    
    # Configuración de Métricas de Calidad
    quality_gate_threshold: float = Field(
        default=80.0,
        env="QUALITY_GATE_THRESHOLD",
        description="Umbral mínimo para el Quality Gate (porcentaje)"
    )
    
    coverage_threshold: float = Field(
        default=70.0,
        env="COVERAGE_THRESHOLD",
        description="Umbral mínimo de cobertura de código (porcentaje)"
    )
    
    duplication_threshold: float = Field(
        default=3.0,
        env="DUPLICATION_THRESHOLD",
        description="Umbral máximo de duplicación de código (porcentaje)"
    )
    
    @field_validator('sonarcloud_token')
    @classmethod
    def validate_token(cls, v):
        """Validar que el token no esté vacío"""
        if not v:
            raise ValueError('El token de SonarCloud es requerido')
        return v
    
    @field_validator('sonarcloud_organization')
    @classmethod
    def validate_organization(cls, v):
        """Validar que la organización no esté vacía"""
        if not v:
            raise ValueError('La organización de SonarCloud es requerida')
        return v
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        """Validar formato de URL de base de datos"""
        if not v.startswith('postgresql://'):
            raise ValueError('La URL de base de datos debe usar el formato postgresql://')
        return v
    
    @field_validator('api_base_url')
    @classmethod
    def validate_api_url(cls, v):
        """Validar URL de la API"""
        if not v.startswith('https://sonarcloud.io/api'):
            raise ValueError('La URL de la API debe ser https://sonarcloud.io/api')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validar nivel de logging"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        if v.upper() not in valid_levels:
            raise ValueError(f'El nivel de logging debe ser uno de: {valid_levels}')
        return v.upper()
    
    @field_validator('batch_size')
    @classmethod
    def validate_batch_size(cls, v):
        """Validar tamaño del lote"""
        if v < 1 or v > 1000:
            raise ValueError('El tamaño del lote debe estar entre 1 y 1000')
        return v
    
    @field_validator('quality_gate_threshold', 'coverage_threshold')
    @classmethod
    def validate_percentage_threshold(cls, v):
        """Validar umbrales de porcentaje"""
        if v < 0 or v > 100:
            raise ValueError('Los umbrales de porcentaje deben estar entre 0 y 100')
        return v
    
    @field_validator('duplication_threshold')
    @classmethod
    def validate_duplication_threshold(cls, v):
        """Validar umbral de duplicación"""
        if v < 0 or v > 100:
            raise ValueError('El umbral de duplicación debe estar entre 0 y 100')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instancia global de configuración
_settings = None


def get_settings() -> Settings:
    """
    Obtener instancia de configuración (singleton)
    
    Returns:
        Settings: Instancia de configuración
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
