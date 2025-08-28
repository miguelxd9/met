"""
Conexión a base de datos PostgreSQL para SonarCloud

Proporciona configuración de conexión, inicialización de base de datos
y gestión de sesiones SQLAlchemy.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from ..config.settings import get_settings
from ..models import Base
from ..utils.logger import get_logger


class DatabaseManager:
    """
    Gestor de conexión a base de datos PostgreSQL
    
    Maneja la configuración de conexión, inicialización de base de datos
    y gestión de sesiones SQLAlchemy.
    """
    
    def __init__(self):
        """Inicializar gestor de base de datos"""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Configurar engine
        self.engine = None
        self.SessionLocal = None
        
        self.logger.debug("DatabaseManager inicializado")
    
    def init_engine(self) -> None:
        """Inicializar engine de SQLAlchemy"""
        try:
            # Configurar engine con pooling
            self.engine = create_engine(
                self.settings.database_url,
                poolclass=NullPool,  # Deshabilitar pooling para evitar problemas
                echo=False,  # No mostrar SQL en logs
                pool_pre_ping=True,  # Verificar conexión antes de usar
                pool_recycle=3600,  # Reciclar conexiones cada hora
            )
            
            # Configurar session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self.logger.info("Engine de base de datos inicializado")
            
        except Exception as e:
            self.logger.error(f"Error al inicializar engine: {str(e)}")
            raise
    
    def create_tables(self) -> None:
        """Crear todas las tablas de la base de datos"""
        try:
            if not self.engine:
                self.init_engine()
            
            # Crear todas las tablas
            Base.metadata.create_all(bind=self.engine)
            
            self.logger.info("Tablas de base de datos creadas exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error al crear tablas: {str(e)}")
            raise
    
    def drop_tables(self) -> None:
        """Eliminar todas las tablas de la base de datos"""
        try:
            if not self.engine:
                self.init_engine()
            
            # Eliminar todas las tablas
            Base.metadata.drop_all(bind=self.engine)
            
            self.logger.info("Tablas de base de datos eliminadas exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error al eliminar tablas: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """
        Obtener sesión de base de datos
        
        Returns:
            Session: Sesión de SQLAlchemy
        """
        if not self.SessionLocal:
            self.init_engine()
        
        return self.SessionLocal()
    
    @contextmanager
    def get_session_context(self) -> Generator[Session, None, None]:
        """
        Context manager para sesiones de base de datos
        
        Yields:
            Session: Sesión de SQLAlchemy
            
        Example:
            with db_manager.get_session_context() as session:
                # Usar sesión
                pass
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """Cerrar conexiones de base de datos"""
        try:
            if self.engine:
                self.engine.dispose()
                self.logger.info("Conexiones de base de datos cerradas")
        except Exception as e:
            self.logger.error(f"Error al cerrar conexiones: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Probar conexión a la base de datos
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            if not self.engine:
                self.init_engine()
            
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            
            self.logger.info("Conexión a base de datos exitosa")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en conexión a base de datos: {str(e)}")
            return False


# Instancia global del gestor de base de datos
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """
    Obtener instancia del gestor de base de datos (singleton)
    
    Returns:
        DatabaseManager: Instancia del gestor
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_database() -> None:
    """Inicializar base de datos"""
    db_manager = get_db_manager()
    db_manager.init_engine()
    db_manager.create_tables()


def close_database() -> None:
    """Cerrar conexiones de base de datos"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None


def get_session() -> Session:
    """
    Obtener sesión de base de datos
    
    Returns:
        Session: Sesión de SQLAlchemy
    """
    db_manager = get_db_manager()
    return db_manager.get_session()


@contextmanager
def get_session_context() -> Generator[Session, None, None]:
    """
    Context manager para sesiones de base de datos
    
    Yields:
        Session: Sesión de SQLAlchemy
    """
    db_manager = get_db_manager()
    with db_manager.get_session_context() as session:
        yield session


def test_database_connection() -> bool:
    """
    Probar conexión a la base de datos
    
    Returns:
        bool: True si la conexión es exitosa
    """
    db_manager = get_db_manager()
    return db_manager.test_connection()
