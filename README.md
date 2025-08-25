# 📊 Métricas DevOps - Sistema de Monitoreo de Bitbucket

Sistema completo para recopilar, procesar y analizar métricas DevOps desde Bitbucket, proporcionando insights valiosos sobre el rendimiento y la calidad del desarrollo de software.

## 🚀 Características

- **Recopilación automática** de datos desde la API de Bitbucket
- **Procesamiento de métricas** de proyectos, repositorios, commits y pull requests
- **Base de datos PostgreSQL** para almacenamiento persistente
- **Análisis de cumplimiento DevOps** con scores de calidad
- **Sistema de logging** robusto y configurable
- **Rate limiting** inteligente para evitar límites de API

## 📋 Prerrequisitos

- Python 3.8+
- PostgreSQL 12+
- Cuenta de Bitbucket con acceso a la API
- Credenciales de Bitbucket (App Password)

## 🛠️ Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio-github>
cd metricas_coe_devops
```

### 2. Crear entorno virtual

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
cd bitbucket
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp env.example .env
```

Editar el archivo `.env` con tus credenciales:

```env
# Bitbucket Configuration
BITBUCKET_USERNAME=tu_usuario
BITBUCKET_APP_PASSWORD=tu_app_password
BITBUCKET_WORKSPACE=tu_workspace

# Database Configuration
DATABASE_URL=postgresql://usuario:password@localhost:5432/metricas_devops

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/bitbucket_metrics.log
```

### 5. Configurar base de datos

```bash
# Crear base de datos PostgreSQL
createdb metricas_devops

# Inicializar tablas
python -c "from src.database.connection import init_database; init_database()"
```

## 📁 Estructura del Proyecto

```
metricas_coe_devops/
├── bitbucket/
│   ├── src/
│   │   ├── api/              # Cliente de API de Bitbucket
│   │   ├── config/           # Configuraciones
│   │   ├── database/         # Conexión y repositorios de BD
│   │   ├── models/           # Modelos SQLAlchemy
│   │   ├── scripts/          # Scripts de procesamiento
│   │   ├── services/         # Servicios de negocio
│   │   └── utils/            # Utilidades (logger, rate limiter)
│   ├── config/               # Archivos de configuración JSON
│   ├── docs/                 # Documentación
│   ├── logs/                 # Archivos de log
│   └── alembic/              # Migraciones de base de datos
```

## 🚀 Uso

### Procesar Workspaces y Proyectos

```bash
python src/scripts/process_workspace_projects.py
```

### Procesar Repositorios de un Proyecto

```bash
python src/scripts/process_project_repositories.py
```

### Procesar Repositorios Generales

```bash
python src/scripts/process_repositories.py
```

### Procesar Configuración de Proyectos

```bash
python src/scripts/process_config_projects.py
```

## 📊 Métricas Disponibles

### Proyectos

- Información básica (nombre, descripción, visibilidad)
- Estadísticas de repositorios
- Fechas de creación y actualización

### Repositorios

- Métricas de tamaño y actividad
- Conteo de commits, branches, tags
- Estadísticas de pull requests
- Score de cumplimiento DevOps

### Commits

- Información de autor y fecha
- Mensajes y cambios
- Relación con repositorios

### Pull Requests

- Estado y tipo
- Información de revisores
- Métricas de tiempo de respuesta

## 🔧 Configuración

### Archivos de Configuración

- `config/projects.json` - Lista de proyectos a procesar
- `config/repositories.json` - Lista de repositorios específicos
- `config/project_repositories.json` - Configuración por proyecto

### Variables de Entorno

| Variable                 | Descripción                                    | Requerido |
| ------------------------ | ---------------------------------------------- | --------- |
| `BITBUCKET_USERNAME`     | Usuario de Bitbucket                           | ✅        |
| `BITBUCKET_APP_PASSWORD` | App Password de Bitbucket                      | ✅        |
| `BITBUCKET_WORKSPACE`    | Workspace de Bitbucket                         | ✅        |
| `DATABASE_URL`           | URL de conexión a PostgreSQL                   | ✅        |
| `LOG_LEVEL`              | Nivel de logging (DEBUG, INFO, WARNING, ERROR) | ❌        |
| `LOG_FILE`               | Archivo de log                                 | ❌        |

## 📈 Análisis de Datos

El sistema proporciona métricas clave para DevOps:

- **Cumplimiento DevOps**: Score basado en README, licencia, CI/CD, etc.
- **Actividad del repositorio**: Frecuencia de commits y pull requests
- **Calidad del código**: Análisis de pull requests y reviews
- **Tendencias temporales**: Evolución de métricas en el tiempo

## 🐛 Solución de Problemas

### Errores Comunes

1. **Error de conexión a Bitbucket**

   - Verificar credenciales en `.env`
   - Comprobar permisos de App Password

2. **Error de base de datos**

   - Verificar conexión PostgreSQL
   - Comprobar que la base de datos existe

3. **Rate limiting**
   - El sistema maneja automáticamente los límites de API
   - Ajustar configuración si es necesario

### Logs

Los logs se guardan en `logs/bitbucket_metrics.log` y contienen información detallada sobre:

- Procesamiento de datos
- Errores y excepciones
- Métricas de rendimiento

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:

- Crear un issue en GitHub
- Contactar al equipo de desarrollo

## 🔄 Roadmap

- [ ] Dashboard web para visualización
- [ ] Alertas automáticas
- [ ] Integración con otros sistemas DevOps
- [ ] Métricas de seguridad
- [ ] Análisis de dependencias
