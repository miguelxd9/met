# Bitbucket DevOps Metrics

Sistema de recolección y análisis de métricas de cumplimiento para equipos DevOps desde repositorios de Bitbucket.

## 🎯 Objetivo

Este proyecto permite obtener métricas de múltiples repositorios de Bitbucket y almacenarlas en PostgreSQL para análisis y reporting.

## 🏗️ Arquitectura

```
bitbucket/
├── src/                    # Código fuente principal
│   ├── api/               # Cliente de la API de Bitbucket
│   ├── database/          # Capa de base de datos
│   ├── models/            # Modelos de datos
│   ├── services/          # Lógica de negocio
│   └── utils/             # Utilidades comunes
├── config/                # Configuraciones
├── scripts/               # Scripts de ejecución
├── tests/                 # Tests unitarios e integración
├── alembic/               # Migraciones de base de datos
└── logs/                  # Logs de la aplicación
```

## 🚀 Características

- **API Client**: Cliente robusto para la API de Bitbucket con manejo de rate limiting
- **Base de Datos**: Almacenamiento en PostgreSQL con SQLAlchemy
- **Métricas**: Recolección de métricas de repositorios, workspaces y proyectos
- **Configuración**: Sistema de configuración flexible con variables de entorno
- **Logging**: Sistema de logging estructurado con Structlog
- **Testing**: Suite completa de tests con pytest

## 📋 Requisitos

- Python 3.13.7
- PostgreSQL 16.10.1
- psycopg-binary 3.2.9 (driver PostgreSQL nativo)
- Pydantic 2.11.7 (validación de datos)
- Cuenta de Bitbucket con acceso a la API

## 🛠️ Instalación

1. **Clonar el repositorio**

```bash
git clone <repository-url>
cd bitbucket
```

2. **Crear entorno virtual**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**

```bash
# Instalación estándar
pip install -r requirements.txt

# Si tienes problemas de compilación, usa solo binarios pre-compilados:
pip install --only-binary :all: -r requirements.txt

> **💡 Nota importante**: Si encuentras errores de compilación (especialmente en Windows), el comando `--only-binary :all:` fuerza la instalación de versiones pre-compiladas, evitando problemas de dependencias nativas.
```

4. **Configurar variables de entorno**

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

5. **Configurar base de datos**

```bash
# Crear base de datos PostgreSQL
createdb bitbucket_metrics

# O ingresar a psql y ejecutar lo siguiente
CREATE DATABASE bitbucket_metrics;

# Ejecutar migraciones
alembic upgrade head
```

## 🔧 Configuración

### Compatibilidad con psycopg 3.x

Este proyecto utiliza **psycopg-binary 3.2.9**, la versión más moderna y recomendada del driver PostgreSQL para Python. Esta versión ofrece:

- ✅ **Mejor rendimiento** que psycopg2
- ✅ **Compatibilidad nativa** con PostgreSQL 16.x
- ✅ **Soporte completo** para tipos de datos modernos
- ✅ **Mejor manejo de conexiones** asíncronas
- ✅ **Configuración automática** de timezone y encoding

### Compatibilidad con Pydantic 2.11.7

Este proyecto utiliza **Pydantic 2.11.7**, la versión más reciente y optimizada del framework de validación de datos. Esta versión ofrece:

- ✅ **Validación de campos** con `@field_validator` (nueva sintaxis)
- ✅ **Configuración de modelo** con `model_config` (nueva sintaxis)
- ✅ **Mejor rendimiento** en validación y serialización
- ✅ **Soporte completo** para tipos de Python 3.13+
- ✅ **Validación automática** de tipos y restricciones

### Variables de Entorno (.env)

```env
# Bitbucket API
BITBUCKET_USERNAME=tu_usuario
BITBUCKET_APP_PASSWORD=tu_app_password
BITBUCKET_WORKSPACE=tu_workspace

# Base de Datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/bitbucket_metrics

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API Configuration
API_RATE_LIMIT=1000
API_TIMEOUT=30
```

## 📊 Uso

### Funcionalidades Principales

El proyecto incluye dos funcionalidades principales de producción:

1. **🔌 Test de Conexión**: Verificar conectividad con Bitbucket
2. **📂 Procesamiento de Repositorios**: Obtener y guardar datos en PostgreSQL

**📚 Para información detallada sobre el uso y configuración, consulta el archivo `docs/FUNCIONALIDADES_PRODUCCION.md`**

### Comandos Básicos

```bash
# Probar conexión con Bitbucket
python src/scripts/test_connection.py

# Procesar repositorios configurados
python src/scripts/process_repositories.py
```

## 📁 Archivos de Configuración

### `config/repositories.json`

Archivo principal que define los repositorios a procesar. Incluye:

- Lista de repositorios con workspace y slug
- Estructura simplificada para fácil mantenimiento

### `.env`

Variables de entorno para configuración:

- Credenciales de Bitbucket
- Configuración de base de datos
- Parámetros de API

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests con coverage
pytest --cov=src

# Ejecutar tests específicos
pytest tests/test_api.py
```

### Verificar compatibilidad básica

```bash
# Probar la configuración y compatibilidad básica (recomendado)
python test_simple.py

# Probar la configuración ultra-simplificada (más confiable)
python test_ultra_simple.py
```

### Verificar compatibilidad con psycopg-binary

```bash
# Probar la configuración y compatibilidad básica (recomendado)
python test_simple.py

# Probar la configuración y compatibilidad (versión 3.2.9 específica)
python test_psycopg_3_2_9.py
```

### Verificar compatibilidad con Pydantic 2.11.7

```bash
# Probar la configuración y compatibilidad con Pydantic (script original)
python test_pydantic2.py

# Probar la configuración y compatibilidad (versión 2.11.7 específica)
python test_pydantic_2_11_7.py
```

## 🔧 Troubleshooting

### Problemas de instalación de dependencias

#### Error: "Microsoft Visual C++ 14.0 is required" o problemas de compilación

```bash
# Solución: Usar solo binarios pre-compilados
pip install --only-binary :all: -r requirements.txt
```

#### Error: "Failed building wheel" o problemas de dependencias nativas

```bash
# Actualizar pip primero
python -m pip install --upgrade pip

# Luego instalar con solo binarios
pip install --only-binary :all: -r requirements.txt
```

### Problemas comunes con psycopg-binary 3.x

#### Error: "No module named 'psycopg'"

```bash
# Asegúrate de instalar la versión correcta
pip install psycopg-binary==3.2.9
```

#### Error: "connection failed" en PostgreSQL 16.x

- Verifica que PostgreSQL 16.x esté ejecutándose
- Confirma que la URL de conexión sea correcta
- Asegúrate de que el usuario tenga permisos en la base de datos

#### Error: "timezone" en conexiones

- psycopg 3.x configura automáticamente el timezone a UTC
- Si necesitas otro timezone, modifica `server_settings` en `src/database/connection.py`

### Problemas específicos de Windows

#### Error: "Microsoft Visual C++ 14.0 is required"

```bash
# Solución recomendada: Usar solo binarios pre-compilados
pip install --only-binary :all: -r requirements.txt

# Alternativa: Instalar Visual Studio Build Tools
# Descargar desde: https://visualstudio.microsoft.com/visual-cpp-build-tools/

> **💡 Nota importante**: `psycopg-binary` es el paquete oficial recomendado por el equipo de psycopg para instalaciones binarias. Es equivalente a `psycopg[binary]` pero con un nombre más claro y directo.

### Diferencias entre psycopg[binary] y psycopg-binary

| Característica | psycopg[binary] | psycopg-binary |
|----------------|------------------|----------------|
| **Nombre** | Sintaxis de extras de pip | Nombre directo del paquete |
| **Instalación** | `pip install psycopg[binary]` | `pip install psycopg-binary` |
| **Recomendación** | Sintaxis estándar | **Oficial del equipo psycopg** |
| **Compatibilidad** | ✅ Total | ✅ Total |
| **Rendimiento** | ✅ Igual | ✅ Igual |

### Versiones de psycopg-binary

| Versión | Características | Compatibilidad |
|----------|----------------|----------------|
| **3.1.18** | Versión estable anterior | ✅ PostgreSQL 12+ |
| **3.2.9** | **Versión actual recomendada** | ✅ **PostgreSQL 12+ (mejorada)** |

### Versiones de Pydantic

| Versión | Características | Compatibilidad |
|----------|----------------|----------------|
| **2.39.0** | Versión estable anterior | ✅ Python 3.8+ |
| **2.11.7** | **Versión actual recomendada** | ✅ **Python 3.8+ (mejorada)** |

### Mejoras en psycopg-binary 3.2.9

La versión **3.2.9** incluye mejoras significativas sobre la 3.1.18:

- ✅ **Mejor rendimiento** en conexiones concurrentes
- ✅ **Soporte mejorado** para PostgreSQL 16.x
- ✅ **Correcciones de bugs** y mejor estabilidad
- ✅ **Mejor manejo** de timeouts y reconexiones
- ✅ **Compatibilidad mejorada** con SQLAlchemy 2.0+

### Mejoras en Pydantic 2.11.7

La versión **2.11.7** incluye mejoras significativas sobre la 2.39.0:

- ✅ **Mejor rendimiento** en validación y serialización
- ✅ **Soporte mejorado** para Python 3.13+
- ✅ **Correcciones de bugs** y mejor estabilidad
- ✅ **Mejor manejo** de tipos complejos y anidados
- ✅ **Compatibilidad mejorada** con frameworks modernos
- ✅ **Validación más rápida** de modelos complejos
- ✅ **Compatibilidad hacia atrás** con código Pydantic 2.x existente
```

#### Error: "Unable to find vcvarsall.bat"

```bash
# Usar solo binarios pre-compilados
pip install --only-binary :all: -r requirements.txt
```

### Problemas específicos de Pydantic 2.11.7

#### Error: "ImportError: cannot import name 'validator' from 'pydantic'"

```bash
# Asegúrate de instalar la versión correcta
pip install pydantic==2.11.7

# Si persiste el problema, reinstala todas las dependencias
pip install --only-binary :all: -r requirements.txt
```

#### Error: "No module named 'psycopg'" o "No module named 'psycopg.adapters'"

```bash
# Asegúrate de instalar la versión correcta
pip install psycopg-binary==3.2.9

# Si persiste el problema, reinstala todas las dependencias
pip install --only-binary :all: -r requirements.txt

# Verificar que se instaló correctamente
python -c "import psycopg; print(f'psycopg version: {psycopg.__version__}')"
```

#### Error: "AttributeError: 'Settings' object has no attribute 'Config'"

```bash
# El código ya está actualizado para usar model_config
# Si tienes código personalizado, cambia:
# class Config: -> model_config = {}
```

#### Error: "TypeError: 'validator' decorator requires a function"

```bash
# Cambia @validator por @field_validator y agrega @classmethod
# @validator('field') -> @field_validator('field') @classmethod
```

## 📈 Métricas Disponibles

### Repositorios

- Información básica (nombre, descripción, lenguaje)
- Estadísticas de commits
- Pull requests abiertos/cerrados
- Branches y tags
- Última actividad

### Workspaces

- Número total de repositorios
- Proyectos activos
- Usuarios colaboradores

### Proyectos

- Repositorios por proyecto
- Métricas agregadas por proyecto

## 🔄 Rate Limiting

El sistema implementa rate limiting inteligente para respetar los límites de la API de Bitbucket:

- Límite por defecto: 1000 requests por hora
- Backoff exponencial en caso de límites excedidos
- Cola de requests para optimizar el uso de la API

## 📝 Logging

El sistema utiliza logging estructurado con Structlog:

- Logs en formato JSON para fácil parsing
- Niveles configurables (DEBUG, INFO, WARNING, ERROR)
- Rotación automática de logs
- Integración con sistemas de monitoreo

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 🆘 Soporte

Para soporte técnico o preguntas:

- Crear un issue en el repositorio
- Contactar al equipo de DevOps
- Revisar la documentación de la API de Bitbucket
