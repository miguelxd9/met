# 📊 Sistema de Recopilación de información de Bitbucket

Sistema para recopilar información de bitbucket.

## 🚀 Características

- **Recopilación automática** de datos desde la API de Bitbucket
- **Almacenamiento estructurado** de proyectos, repositorios, commits y pull requests
- **Base de datos SQL Server Azure** para almacenamiento persistente
- **Conexión ODBC** para máxima compatibilidad y rendimiento
- **Sistema de logging** robusto y configurable
- **Rate limiting** inteligente para evitar límites de API

## 📋 Prerrequisitos

- Python 3.8+
- SQL Server Azure (Base de datos en la nube)
- Microsoft ODBC Driver 18 for SQL Server
- Cuenta de Bitbucket con acceso a la API
- Credenciales de Bitbucket (App Password)

- **Windows:**

1. Descargar desde: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
2. Instalar el driver manualmente

- **Linux (Ubuntu/Debian):**

```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
apt-get install -y unixodbc-dev
```

- **Linux (RHEL/CentOS):**

```bash
curl https://packages.microsoft.com/config/rhel/8/prod.repo > /etc/yum.repos.d/mssql-release.repo
ACCEPT_EULA=Y yum install -y msodbcsql18
yum install -y unixODBC-devel
```

## ⚡ Instalación Rápida

```bash
# 1. Clonar y configurar entorno
git clone <tu-repositorio>
cd bitbucket
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux

# 2. Instalar dependencias
pip install -r requirements.txt

# En caso existan problemas de compilación, usar solo binarios pre-compilados
pip install --only-binary :all: -r requirements.txt

# 3. Configurar variables de entorno
cp env.example .env
# Editar .env con tus credenciales

# 4. Ejecutar migraciones
python -m alembic upgrade head

# 5. Probar conexión con la API de Bitbucket
python -m src.scripts.test_connection
```

#### Verificar instalación ODBC (Opcional)

```bash
python install_odbc.py
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

### Probar conexión completa

```bash
# Probar conexión a Bitbucket y base de datos
python -m src.scripts.test_connection
```

### Ejecutar scripts de procesamiento

#### Procesar Workspaces y Proyectos

```bash
python src/scripts/process_workspace_projects.py
```

#### Procesar Repositorios

```bash
python src/scripts/process_repositories.py
```

## 📊 Datos Recopilados

### Proyectos

- Información básica (nombre, descripción, visibilidad)
- Estadísticas de repositorios
- Fechas de creación y actualización

### Repositorios

- Información de tamaño y actividad
- Conteo de commits, branches, tags
- Estado de pull requests
- Información de configuración

### Commits

- Información de autor y fecha
- Mensajes y cambios
- Relación con repositorios

### Pull Requests

- Estado y tipo
- Información de revisores
- Fechas de creación y cierre

## 🔧 Configuración

### Archivos de Configuración

- `config/repositories.json` - Lista de repositorios específicos

### Variables de Entorno

| Variable                      | Descripción                                    | Requerido |
| ----------------------------- | ---------------------------------------------- | --------- |
| `BITBUCKET_USERNAME`          | Usuario de Bitbucket                           | ✅        |
| `BITBUCKET_APP_PASSWORD`      | App Password de Bitbucket                      | ✅        |
| `BITBUCKET_WORKSPACE`         | Workspace de Bitbucket                         | ✅        |
| `DATABASE_URL`                | URL de conexión a SQL Server Azure             | ✅        |
| `API_BASE_URL`                | URL base de la API de Bitbucket                | ❌        |
| `API_RATE_LIMIT`              | Límite de requests por hora                    | ❌        |
| `API_TIMEOUT`                 | Timeout en segundos para requests              | ❌        |
| `API_RETRY_ATTEMPTS`          | Número de intentos de reintento                | ❌        |
| `LOG_LEVEL`                   | Nivel de logging (DEBUG, INFO, WARNING, ERROR) | ❌        |
| `LOG_FORMAT`                  | Formato de logging (json, console)             | ❌        |
| `LOG_FILE`                    | Archivo de log                                 | ❌        |
| `METRICS_COLLECTION_INTERVAL` | Intervalo en segundos para recolección         | ❌        |
| `BATCH_SIZE`                  | Tamaño del lote para procesamiento             | ❌        |

## 📈 Almacenamiento de Datos

El sistema recopila y almacena información clave de Bitbucket:

- **Información de proyectos**: Workspaces, proyectos y su configuración
- **Datos de repositorios**: Código fuente, configuración y estado
- **Historial de commits**: Cambios, autores y fechas
- **Pull Requests**: Estado, revisores y flujo de trabajo

### Logs

Los logs se guardan en `logs/bitbucket_metrics.log` y contienen información detallada sobre:

- Procesamiento de datos
- Errores y excepciones

## 📞 Soporte

Para soporte técnico o preguntas:

- Contactar al equipo de DevOps

## 🗄️ Configuración SQL Server Azure con AAD Interactive

### Requisitos de Azure

1. **SQL Server Azure** configurado y funcionando
2. **Base de datos** `bitbucket_metrics` creada
3. **Firewall** configurado para permitir conexiones desde tu IP
4. **Azure Active Directory (AAD)** configurado para autenticación
5. **Tu cuenta de usuario** debe tener acceso a la base de datos

### Configuración de AAD Interactive

El proyecto está configurado para usar **Azure Active Directory Interactive Authentication**, que:

- ✅ **No requiere** almacenar contraseñas en archivos de configuración
- ✅ **Abre automáticamente** una ventana del navegador para autenticación
- ✅ **Usa tu cuenta de Azure** para acceder a la base de datos
- ✅ **Maneja automáticamente** la renovación de tokens
- ✅ **Es más seguro** que usar credenciales estáticas

### Configuración de la Cadena de Conexión

Tu `DATABASE_URL` debe tener esta estructura:

```env
DATABASE_URL=mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 18 for SQL Server};SERVER=tu-servidor.database.windows.net;DATABASE=bitbucket_metrics;Authentication=ActiveDirectoryInteractive;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
```

**Parámetros importantes:**

- `SERVER`: Tu servidor SQL Server Azure
- `DATABASE`: Nombre de tu base de datos
- `Authentication=ActiveDirectoryInteractive`: Habilita AAD Interactive
- `Encrypt=yes`: Encriptación obligatoria para Azure

### Estructura de Tablas

El sistema crea automáticamente las siguientes tablas:

- **workspaces**: Información de workspaces de Bitbucket
- **projects**: Proyectos dentro de los workspaces
- **repositories**: Repositorios de código
- **commits**: Información de commits
- **pull_requests**: Pull requests y su información
- **branches**: Ramas de los repositorios

### Migraciones

Las migraciones se ejecutan automáticamente usando Alembic:

```bash
# Ver estado de migraciones
python -m alembic current

# Ejecutar migraciones pendientes
python -m alembic upgrade head

# Crear nueva migración (si es necesario)
python -m alembic revision -m "descripcion_cambio"
```

### Monitoreo de Conexión

Para verificar que todo funciona correctamente:

```bash
# Probar conexión AAD Interactive (Recomendado)
python test_aad_connection.py

# Probar solo conexión a base de datos
python -m src.scripts.test_connection --database-only

# Probar conexión completa (Bitbucket + Base de datos)
python -m src.scripts.test_connection
```

**Nota:** El script `test_aad_connection.py` está específicamente diseñado para probar la conexión AAD Interactive y te dará información detallada sobre tu conexión.
