"""
Configuración de conexión a la base de datos PostgreSQL
"""

from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Gestor de conexiones a la base de datos PostgreSQL
    
    Maneja:
    - Conexión a PostgreSQL
    - Pool de conexiones
    - Sesiones de SQLAlchemy
    - Configuración de la base de datos
    """
    
    def __init__(self):
        """Inicializar gestor de base de datos"""
        self.settings = get_settings()
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def init_database(self) -> None:
        """Inicializar conexión a la base de datos"""
        if self._initialized:
            logger.warning("Base de datos ya inicializada")
            return
        
        try:
            # Crear engine de SQLAlchemy
            # Forzar el uso de psycopg en lugar de psycopg2
            database_url = self.settings.database_url
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+psycopg://")
            
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,  # Cambiar a True para debug
                connect_args={
                    "connect_timeout": 10,
                    "options": "-c application_name=bitbucket_metrics -c timezone=UTC"
                }
            )
            
            # Configurar pool de conexiones
            self._configure_pool()
            
            # Crear sesión local
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Verificar conexión
            self._test_connection()
            
            self._initialized = True
            logger.info(f"Base de datos inicializada exitosamente - URL: {self.settings.database_url}, Pool: 10, Overflow: 20")
            
        except Exception as e:
            logger.error(f"Error al inicializar base de datos: {str(e)}, URL: {self.settings.database_url}")
            raise
    
    def _configure_pool(self) -> None:
        """Configurar pool de conexiones"""
        if not self.engine:
            return
        
        # Configurar eventos del pool
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Configurar parámetros de PostgreSQL"""
            if hasattr(dbapi_connection, 'set_session'):
                # Configurar timezone y encoding
                dbapi_connection.set_session(
                    autocommit=False,
                    readonly=False,
                    deferrable=False
                )
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Evento al obtener conexión del pool"""
            logger.debug("Conexión obtenida del pool")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Evento al devolver conexión al pool"""
            logger.debug("Conexión devuelta al pool")
    
    def _test_connection(self) -> None:
        """Probar conexión a la base de datos"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
                logger.debug("Conexión a base de datos probada exitosamente")
        except Exception as e:
            logger.error(f"Error al probar conexión a base de datos: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """
        Obtener sesión de base de datos
        
        Returns:
            Session: Sesión de SQLAlchemy
            
        Raises:
            RuntimeError: Si la base de datos no está inicializada
        """
        if not self._initialized:
            raise RuntimeError("Base de datos no inicializada. Llama a init_database() primero")
        
        return self.SessionLocal()
    
    def close(self) -> None:
        """Cerrar conexiones a la base de datos"""
        if self.engine:
            self.engine.dispose()
            self._initialized = False
            logger.info("Conexiones a base de datos cerradas")
    
    def get_engine_info(self) -> dict:
        """
        Obtener información del engine de base de datos
        
        Returns:
            dict: Información del engine
        """
        if not self.engine:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized" if self._initialized else "error",
            "pool_size": self.engine.pool.size(),
            "checked_in": self.engine.pool.checkedin(),
            "checked_out": self.engine.pool.checkedout(),
            "overflow": self.engine.pool.overflow(),
            "invalid": self.engine.pool.invalid()
        }


# Instancia global del gestor de base de datos
_db_manager = DatabaseManager()


def init_database() -> None:
    """
    Inicializar base de datos (función de conveniencia)
    
    Esta función debe ser llamada al inicio de la aplicación
    """
    _db_manager.init_database()


def get_database_session() -> Session:
    """
    Obtener sesión de base de datos (función de conveniencia)
    
    Returns:
        Session: Sesión de SQLAlchemy
    """
    return _db_manager.get_session()


@contextmanager
def get_db_session():
    """
    Context manager para sesiones de base de datos
    
    Usage:
        with get_db_session() as session:
            # Usar session
            pass
    """
    session = get_database_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def close_database() -> None:
    """
    Cerrar conexiones a la base de datos (función de conveniencia)
    
    Esta función debe ser llamada al finalizar la aplicación
    """
    _db_manager.close()


def get_database_info() -> dict:
    """
    Obtener información de la base de datos (función de conveniencia)
    
    Returns:
        dict: Información de la base de datos
    """
    return _db_manager.get_engine_info()
