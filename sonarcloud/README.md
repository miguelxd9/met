# SonarCloud Metrics DevOps

Sistema de recolección y análisis de métricas de calidad de código desde SonarCloud API.

## Descripción

Este proyecto permite la integración con la API oficial de SonarCloud para recopilar métricas de calidad de código de múltiples proyectos y organizaciones. El sistema incluye:

- **Recolección automática** de métricas de proyectos
- **Almacenamiento en PostgreSQL** con migraciones automáticas
- **Análisis de calidad** con scoring personalizado
- **Rate limiting inteligente** para respetar límites de API
- **Procesamiento por lotes** para optimizar rendimiento
- **Reportes y dashboards** de métricas de calidad

## Características Principales

### Métricas Recolectadas

- **Cobertura de código** (coverage %)
- **Duplicación de código** (duplications %)
- **Calificaciones de calidad** (maintainability, reliability, security ratings)
- **Conteo de issues** (bugs, vulnerabilities, code smells, new issues)
- **Security hotspots** con niveles de vulnerabilidad
- **Quality Gate status** y alertas
- **Líneas de código** (LOC, NCLOC)

### Ordenamiento por Prioridad

Los proyectos se ordenan automáticamente por:

1. **Coverage** (descendente)
2. **Duplicaciones** (ascendente)
3. **Issues nuevas** (ascendente)
4. **Severidad de hotspots** (critical > high > medium > low)

## Instalación

### Prerrequisitos

- Python 3.8+
- PostgreSQL 12+
- Token de acceso a SonarCloud API

### Configuración

1. **Clonar el repositorio**

```bash
git clone <repository-url>
cd sonarcloud
```

2. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**

```bash
cp env.example .env
```

Editar `.env` con tus credenciales:

```env
# SonarCloud Configuration
SONARCLOUD_TOKEN=your_sonarcloud_token
SONARCLOUD_ORGANIZATION=your_organization_key

# Database Configuration
DATABASE_URL=postgresql://localhost:5432/sonarcloud_metrics

# API Configuration
API_BASE_URL=https://sonarcloud.io/api
BATCH_SIZE=100

# Quality Thresholds
QUALITY_GATE_THRESHOLD=80.0
COVERAGE_THRESHOLD=70.0
DUPLICATION_THRESHOLD=3.0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/sonarcloud_metrics.log
```

4. **Crear base de datos**

```sql
CREATE DATABASE sonarcloud_metrics;
```

5. **Ejecutar migraciones**

```bash
alembic upgrade head
```

## Uso

### Scripts Principales

#### 1. Recolección de Métricas

```bash
# Sincronizar organización completa
python -m src.scripts.collect_metrics --organization my-org --sync-all

# Sincronizar proyecto específico
python -m src.scripts.collect_metrics --organization my-org --project my-project

# Generar solo reportes
python -m src.scripts.collect_metrics --organization my-org --reports-only

# Especificar tamaño de lote
python -m src.scripts.collect_metrics --organization my-org --sync-all --batch-size 50
```

#### 2. Prueba de Conexión

```bash
# Probar todas las conexiones
python -m src.scripts.test_connection --organization my-org

# Probar solo configuración
python -m src.scripts.test_connection --config-only

# Probar solo base de datos
python -m src.scripts.test_connection --db-only

# Probar solo API
python -m src.scripts.test_connection --api-only --organization my-org
```

### Uso Programático

```python
from src.services import ProjectService, OrganizationService, MetricsService
from src.database import get_session_context

# Inicializar servicios
project_service = ProjectService()
org_service = OrganizationService()
metrics_service = MetricsService()

# Sincronizar organización
async with get_session_context() as session:
    result = await project_service.sync_organization_projects(
        session, "my-organization", batch_size=100
    )
    print(f"Proyectos sincronizados: {result['total_projects']}")

# Obtener proyectos por prioridad
async with get_session_context() as session:
    projects = await project_service.get_projects_by_priority(
        session, "my-organization", limit=10
    )
    for project in projects:
        print(f"{project.name}: {project.get_quality_score():.2f}")

# Análisis de métricas
async with get_session_context() as session:
    summary = metrics_service.get_quality_metrics_summary(
        session, "my-organization"
    )
    print(f"Promedio de cobertura: {summary['avg_coverage']:.2f}%")
```

## Estructura del Proyecto

```
sonarcloud/
├── src/
│   ├── api/
│   │   └── sonarcloud_client.py      # Cliente de API de SonarCloud
│   ├── config/
│   │   └── settings.py               # Configuración con Pydantic
│   ├── database/
│   │   ├── connection.py             # Gestión de conexión a BD
│   │   └── repositories.py           # Repositorios de datos
│   ├── models/
│   │   ├── base.py                   # Modelo base
│   │   ├── organization.py           # Modelo de organizaciones
│   │   ├── project.py                # Modelo de proyectos
│   │   ├── quality_gate.py           # Modelo de quality gates
│   │   ├── metric.py                 # Modelo de métricas
│   │   ├── issue.py                  # Modelo de issues
│   │   └── security_hotspot.py       # Modelo de security hotspots
│   ├── services/
│   │   ├── project_service.py        # Lógica de negocio de proyectos
│   │   ├── organization_service.py   # Lógica de negocio de organizaciones
│   │   └── metrics_service.py        # Análisis de métricas
│   ├── scripts/
│   │   ├── collect_metrics.py        # Script principal de recolección
│   │   └── test_connection.py        # Script de prueba de conexión
│   └── utils/
│       ├── logger.py                 # Configuración de logging
│       └── rate_limiter.py           # Control de rate limiting
├── alembic/                          # Migraciones de base de datos
├── logs/                             # Archivos de log
├── requirements.txt                  # Dependencias de Python
├── env.example                       # Ejemplo de variables de entorno
└── README.md                         # Este archivo
```

## Modelos de Datos

### Organization

- `uuid`, `key`, `name`: Identificadores de la organización
- `sonarcloud_id`: ID interno de SonarCloud
- `created_at`, `updated_at`: Timestamps de auditoría

### Project

- `uuid`, `key`, `name`: Identificadores del proyecto
- `organization_id`: Relación con organización
- `visibility`: Visibilidad del proyecto
- `last_analysis_date`: Última fecha de análisis
- **Métricas de calidad**: coverage, duplications, ratings, counts
- `alert_status`, `quality_gate_status`: Estados de alerta

### QualityGate

- `name`, `status`: Nombre y estado del quality gate
- `evaluated_at`: Fecha de evaluación
- `organization_id`, `project_id`: Relaciones

### Metric

- `key`, `name`: Identificadores de la métrica
- `value`, `string_value`: Valores numérico y string
- `data_type`, `domain`, `direction`: Metadatos de la métrica
- `project_id`: Relación con proyecto

### Issue

- `uuid`, `rule`: Identificadores del issue
- `severity`, `type`, `status`: Clasificación del issue
- `component`, `line`, `message`: Detalles del issue
- `author`, `assignee`: Responsables
- `created_at`, `updated_at`, `closed_at`: Timestamps
- `project_id`: Relación con proyecto

### SecurityHotspot

- `uuid`, `rule_key`: Identificadores del hotspot
- `vulnerability_probability`: Probabilidad de vulnerabilidad
- `security_category`: Categoría de seguridad
- `status`, `resolution`: Estado y resolución
- `component`, `line`, `message`: Detalles del hotspot
- `author`, `assignee`: Responsables
- `created_at`, `updated_at`, `resolved_at`: Timestamps
- `project_id`: Relación con proyecto

## Configuración Avanzada

### Rate Limiting

El sistema incluye rate limiting inteligente para respetar los límites de la API de SonarCloud:

- **Límite por defecto**: 1000 requests por hora
- **Backoff exponencial**: Reintentos automáticos con espera progresiva
- **Pausas automáticas**: Detección y manejo de límites de API

### Procesamiento por Lotes

- **Tamaño de lote configurable**: Por defecto 100 proyectos
- **Procesamiento asíncrono**: Múltiples requests concurrentes
- **Manejo de errores**: Continuación automática en caso de fallos

### Logging

- **Formato estructurado**: JSON para fácil parsing
- **Niveles configurables**: DEBUG, INFO, WARNING, ERROR
- **Archivos de log**: Rotación automática
- **Console output**: Con colores usando Rich

## API de SonarCloud

El sistema utiliza los siguientes endpoints de la API oficial:

- `GET /organizations/{organization}`: Información de organización
- `GET /projects/search`: Lista de proyectos
- `GET /measures/component`: Métricas de proyecto
- `GET /issues/search`: Issues del proyecto
- `GET /hotspots/search`: Security hotspots
- `GET /qualitygates/project_status`: Estado de quality gate

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para soporte técnico o preguntas:

- Crear un issue en el repositorio
- Contactar al equipo de desarrollo
- Revisar la documentación de la API de SonarCloud
