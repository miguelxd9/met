# 🚀 Funcionalidades de Producción - Bitbucket DevOps Metrics

Este documento describe las funcionalidades de producción implementadas para el proyecto de métricas DevOps de Bitbucket.

## 📋 Tabla de Contenidos

1. [Funcionalidad de Prueba de Conexión](#funcionalidad-de-prueba-de-conexión)
2. [Funcionalidad de Procesamiento de Repositorios](#funcionalidad-de-procesamiento-de-repositorios)
3. [Funcionalidad de Procesamiento de Proyectos del Workspace](#funcionalidad-de-procesamiento-de-proyectos-del-workspace)
4. [Funcionalidad de Procesamiento de Proyectos Configurados](#funcionalidad-de-procesamiento-de-proyectos-configurados)
5. [Funcionalidad de Procesamiento de Repositorios del Proyecto](#funcionalidad-de-procesamiento-de-repositorios-del-proyecto)
6. [Estructura de Archivos de Configuración](#estructura-de-archivos-de-configuración)
7. [Comandos de Ejecución](#comandos-de-ejecución)
8. [Validaciones y Seguridad](#validaciones-y-seguridad)
9. [Manejo de Errores](#manejo-de-errores)
10. [Logs y Monitoreo](#logs-y-monitoreo)

---

## 🔌 Funcionalidad de Prueba de Conexión

### Descripción

Esta funcionalidad permite verificar que la conexión con la API de Bitbucket esté funcionando correctamente antes de ejecutar operaciones de producción.

### Características

- ✅ **Verificación de configuración**: Muestra la configuración actual del proyecto
- ✅ **Prueba de autenticación**: Verifica que las credenciales sean válidas
- ✅ **Test de endpoints**: Prueba la conectividad con endpoints básicos de Bitbucket
- ✅ **Información del workspace**: Obtiene y muestra información del workspace configurado
- ✅ **Estado del rate limiter**: Muestra el estado actual del limitador de velocidad

### Archivo

- **Ruta**: `src/scripts/test_connection.py`
- **Tipo**: Script de prueba independiente
- **Dependencias**: Solo requiere configuración básica y credenciales válidas

### Comando de Ejecución

```bash
python src/scripts/test_connection.py
```

### Salida Esperada

```
🚀 Test de Conexión con Bitbucket
==================================================

🔍 Probando conexión con Bitbucket...
==================================================
🌐 API Base URL: https://api.bitbucket.org/2.0
👤 Usuario: mdelacruzsangay
⏱️  Timeout: 30 segundos
🚦 Rate Limit: 1000 requests/hora

🔌 Creando cliente de Bitbucket...
✅ Cliente creado exitosamente

📡 Probando conexión básica...
🏢 Obteniendo información del workspace: ibkteam
✅ Workspace obtenido exitosamente
   📝 Nombre: Ibkteam
   🆔 ID: 12345678
   🔒 Privado: true
   🌐 Website: https://ibkteam.bitbucket.org
   📍 Ubicación: Lima, Perú

🚦 Estado del Rate Limiter:
   ⏰ Requests restantes: 950
   🔄 Reset time: 2025-08-25 04:00:00

🎉 ¡Conexión con Bitbucket probada exitosamente!
✅ Todas las funcionalidades básicas están funcionando correctamente

🎯 Resultado: CONEXIÓN EXITOSA
   El proyecto está configurado correctamente para trabajar con Bitbucket

==================================================
```

---

## 📂 Funcionalidad de Procesamiento de Repositorios

### Descripción

Esta funcionalidad principal permite procesar y guardar información detallada de múltiples repositorios de Bitbucket en la base de datos PostgreSQL. Los repositorios se definen en un archivo de configuración JSON y se procesan de forma secuencial.

### Características

- ✅ **Procesamiento por lotes**: Procesa múltiples repositorios desde un archivo de configuración
- ✅ **Creación inteligente**: Crea workspaces, proyectos y repositorios solo si no existen
- ✅ **Actualización automática**: Actualiza datos existentes si el repositorio ya está registrado
- ✅ **Validación de identidad única**: Garantiza que no existan repositorios duplicados por slug
- ✅ **Manejo de transacciones**: Usa transacciones de base de datos para consistencia
- ✅ **Estadísticas detalladas**: Proporciona resumen completo del procesamiento
- ✅ **Manejo de errores robusto**: Continúa procesando otros repositorios si uno falla

### Archivo

- **Ruta**: `src/scripts/process_repositories.py`
- **Tipo**: Script principal de producción
- **Dependencias**: Base de datos PostgreSQL, configuración de Bitbucket, archivo JSON

### Comando de Ejecución

```bash
python src/scripts/process_repositories.py
```

### Salida Esperada

```
🚀 Procesador de Repositorios de Bitbucket
============================================================

🚀 Iniciando procesamiento de repositorios...
============================================================
📋 Configuración cargada desde: config/repositories.json
   📊 Total de repositorios: 3

🗄️  Inicializando base de datos...
✅ Base de datos inicializada
🔌 Obteniendo sesión de base de datos...
✅ Sesión obtenida

📋 [1/3] Procesando repositorio...
🔍 Procesando: ibk-banca-movil-ios
   🏢 Workspace: ibkteam
   📡 Obteniendo datos desde Bitbucket...
   ✅ Datos obtenidos de Bitbucket
   🏢 Procesando Workspace...
      ✅ Workspace 'ibkteam' encontrado
   📁 Procesando Project...
      ✅ Project 'APP' actualizado
   📂 Procesando Repository...
      ✅ Repository 'ibk-banca-movil-ios' actualizado
   ✅ Repositorio procesado exitosamente

📋 [2/3] Procesando repositorio...
🔍 Procesando: ibk-banca-movil-android
   🏢 Workspace: ibkteam
   📡 Obteniendo datos desde Bitbucket...
   ✅ Datos obtenidos de Bitbucket
   🏢 Procesando Workspace...
      ✅ Workspace 'ibkteam' encontrado
   📁 Procesando Project...
      ✅ Project 'APP' encontrado
   📂 Procesando Repository...
      ✅ Repository 'ibk-banca-movil-android' creado
   ✅ Repositorio procesado exitosamente

📋 [3/3] Procesando repositorio...
🔍 Procesando: ibk-web-portal
   🏢 Workspace: ibkteam
   📡 Obteniendo datos desde Bitbucket...
   ✅ Datos obtenidos de Bitbucket
   🏢 Procesando Workspace...
      ✅ Workspace 'ibkteam' encontrado
   📁 Procesando Project...
      ✅ Project 'WEB' creado
   📂 Procesando Repository...
      ✅ Repository 'ibk-web-portal' creado
   ✅ Repositorio procesado exitosamente

🎯 RESUMEN DEL PROCESAMIENTO
========================================
📊 Total procesados: 3
🆕 Total creados: 3
🔄 Total actualizados: 0
❌ Total errores: 0

🎉 ¡Procesamiento completado!
🔌 Sesión de base de datos cerrada

✅ Proceso completado exitosamente
   Los repositorios han sido guardados/actualizados en la base de datos

============================================================
```

---

## 📄 Estructura del Archivo de Configuración

### Archivo

- **Ruta**: `config/repositories.json`
- **Formato**: JSON estándar
- **Codificación**: UTF-8

### Estructura Completa

```json
{
  "repositories": [
    {
      "workspace_slug": "ibkteam",
      "repository_slug": "ibk-banca-movil-ios"
    },
    {
      "workspace_slug": "ibkteam",
      "repository_slug": "ibk-banca-movil-android"
    },
    {
      "workspace_slug": "ibkteam",
      "repository_slug": "ibk-web-portal"
    }
  ]
}
```

#### Campos del Repositorio

| Campo             | Tipo   | Requerido | Descripción                                      |
| ----------------- | ------ | --------- | ------------------------------------------------ |
| `workspace_slug`  | string | ✅        | Identificador único del workspace en Bitbucket   |
| `repository_slug` | string | ✅        | Identificador único del repositorio en Bitbucket |

### 2. Archivo: `config/projects.json`

Este archivo define los proyectos específicos que se procesarán. Cada proyecto debe especificar su workspace y clave.

#### Estructura JSON

```json
{
  "projects": [
    {
      "workspace_slug": "ibkteam",
      "project_key": "IBK-MOBILE"
    },
    {
      "workspace_slug": "ibkteam",
      "project_key": "IBK-WEB"
    },
    {
      "workspace_slug": "ibkteam",
      "project_key": "IBK-API"
    }
  ]
}
```

#### Campos del Proyecto

| Campo            | Tipo   | Requerido | Descripción                                    |
| ---------------- | ------ | --------- | ---------------------------------------------- |
| `workspace_slug` | string | ✅        | Identificador único del workspace en Bitbucket |
| `project_key`    | string | ✅        | Clave única del proyecto en Bitbucket          |

### 3. Archivo: `config/project_repositories.json`

Este archivo define un proyecto específico del cual se obtendrán todos sus repositorios.

#### Estructura JSON

```json
{
  "project": {
    "workspace_slug": "ibkteam",
    "project_key": "IBK-MOBILE"
  }
}
```

#### Campos del Proyecto

| Campo            | Tipo   | Requerido | Descripción                                    |
| ---------------- | ------ | --------- | ---------------------------------------------- |
| `workspace_slug` | string | ✅        | Identificador único del workspace en Bitbucket |
| `project_key`    | string | ✅        | Clave única del proyecto en Bitbucket          |

---

## ⌨️ Comandos de Ejecución

### 1. Prueba de Conexión

```bash
# Desde el directorio raíz del proyecto
python src/scripts/test_connection.py

# O desde cualquier ubicación
python /ruta/completa/bitbucket/src/scripts/test_connection.py
```

### 2. Procesamiento de Repositorios

```bash
# Desde el directorio raíz del proyecto
python src/scripts/process_repositories.py

# O desde cualquier ubicación
python /ruta/completa/bitbucket/src/scripts/process_repositories.py
```

### 3. Procesamiento de Proyectos del Workspace

```bash
# Desde el directorio raíz del proyecto
python src/scripts/process_workspace_projects.py

# O desde cualquier ubicación
python /ruta/completa/bitbucket/src/scripts/process_workspace_projects.py
```

### 4. Procesamiento de Proyectos Configurados

```bash
# Desde el directorio raíz del proyecto
python src/scripts/process_config_projects.py

# O desde cualquier ubicación
python /ruta/completa/bitbucket/src/scripts/process_config_projects.py
```

### 5. Procesamiento de Repositorios del Proyecto

```bash
# Desde el directorio raíz del proyecto
python src/scripts/process_project_repositories.py

# O desde cualquier ubicación
python /ruta/completa/bitbucket/src/scripts/process_project_repositories.py
```

### 6. Verificación de Dependencias

```bash
# Verificar que todas las dependencias estén instaladas
pip list | findstr -i "sqlalchemy\|psycopg\|pydantic\|httpx"

# Verificar versión de Python
python --version
```

---

## 🔒 Validaciones y Seguridad

### Validaciones de Entrada

- ✅ **Formato JSON**: Valida que el archivo de configuración sea JSON válido
- ✅ **Campos requeridos**: Verifica que los campos obligatorios estén presentes
- ✅ **Tipos de datos**: Valida que los campos sean del tipo correcto
- ✅ **Estructura de archivos**: Valida la estructura específica de cada archivo de configuración

### Validaciones de Base de Datos

- ✅ **Identidad única por UUID**: Garantiza que no existan registros duplicados
- ✅ **Integridad referencial**: Mantiene relaciones entre workspace, project y repository
- ✅ **Transacciones**: Usa transacciones para garantizar consistencia de datos
- ✅ **Rollback automático**: Revierte cambios si ocurre un error
- ✅ **Actualización inteligente**: Actualiza registros existentes en lugar de crear duplicados

### Validaciones de API

- ✅ **Rate limiting**: Respeta los límites de velocidad de la API de Bitbucket
- ✅ **Timeout**: Maneja timeouts de conexión de forma elegante
- ✅ **Reintentos**: Implementa reintentos automáticos para errores temporales
- ✅ **Validación de respuestas**: Verifica que las respuestas de la API sean válidas

---

## ⚠️ Manejo de Errores

### Tipos de Errores Manejados

#### 1. Errores de Configuración

- **Archivo no encontrado**: `FileNotFoundError`
- **JSON inválido**: `json.JSONDecodeError`
- **Campos faltantes**: Validación personalizada

#### 2. Errores de Base de Datos

- **Conexión fallida**: `sqlalchemy.exc.OperationalError`
- **Restricciones violadas**: `psycopg.errors.NotNullViolation`
- **Transacciones fallidas**: Rollback automático

#### 3. Errores de API

- **Autenticación fallida**: `httpx.HTTPStatusError` (401)
- **Rate limit excedido**: `httpx.HTTPStatusError` (429)
- **Recurso no encontrado**: `httpx.HTTPStatusError` (404)
- **Timeout de conexión**: `httpx.TimeoutException`

#### 4. Errores del Sistema

- **Memoria insuficiente**: `MemoryError`
- **Permisos de archivo**: `PermissionError`
- **Errores de red**: `httpx.ConnectError`

### Estrategias de Recuperación

- 🔄 **Reintentos automáticos**: Para errores temporales de red
- 🚫 **Continuación**: Procesa otros repositorios si uno falla
- 📊 **Registro de errores**: Mantiene estadísticas de errores
- 🔌 **Reconexión**: Reintenta conexión a base de datos si falla

---

## 📊 Logs y Monitoreo

### Niveles de Log

- **INFO**: Operaciones normales y progreso del proceso
- **WARNING**: Situaciones que requieren atención pero no detienen el proceso
- **ERROR**: Errores que impiden completar una operación específica
- **DEBUG**: Información detallada para diagnóstico (solo en desarrollo)

### Información Registrada

- 📅 **Timestamps**: Fecha y hora de cada operación
- 🔍 **Operaciones**: Tipo de operación realizada
- 📊 **Estadísticas**: Conteos de éxito, errores y actualizaciones
- ⚠️ **Errores**: Detalles completos de errores con stack traces
- 🚦 **Rate Limiting**: Estado del limitador de velocidad de la API

### Monitoreo en Tiempo Real

- 📈 **Progreso**: Muestra avance del procesamiento en tiempo real
- ⏱️ **Tiempo**: Tiempo transcurrido y estimado de finalización
- 🎯 **Estado**: Estado actual de cada repositorio siendo procesado
- 📊 **Métricas**: Estadísticas acumulativas durante el proceso

---

## 🚀 Casos de Uso

### 1. Configuración Inicial

```bash
# 1. Verificar conexión
python src/scripts/test_connection.py

# 2. Si la conexión es exitosa, procesar repositorios
python src/scripts/process_repositories.py
```

### 2. Actualización Regular

```bash
# Ejecutar periódicamente para mantener datos actualizados
python src/scripts/process_repositories.py
```

### 3. Agregar Nuevos Repositorios

```bash
# 1. Editar config/repositories.json para agregar nuevos repositorios
# 2. Ejecutar el procesador
python src/scripts/process_repositories.py
```

### 4. Procesar Proyectos del Workspace

```bash
# Ejecutar para obtener todos los proyectos del workspace configurado
python src/scripts/process_workspace_projects.py
```

### 5. Procesar Proyectos Específicos

```bash
# 1. Editar config/projects.json para definir proyectos específicos
# 2. Ejecutar el procesador
python src/scripts/process_config_projects.py
```

### 6. Procesar Repositorios de un Proyecto

```bash
# 1. Editar config/project_repositories.json para definir el proyecto
# 2. Ejecutar el procesador
python src/scripts/process_project_repositories.py
```

### 7. Diagnóstico de Problemas

```bash
# 1. Verificar conexión
python src/scripts/test_connection.py

# 2. Si hay errores, revisar logs y configuración
# 3. Corregir problemas y volver a probar
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Configuración de Bitbucket
BITBUCKET_USERNAME=tu_usuario
BITBUCKET_APP_PASSWORD=tu_app_password
API_BASE_URL=https://api.bitbucket.org/2.0

# Configuración de Base de Datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/bitbucket_metrics

# Configuración de API
API_TIMEOUT=30
API_RATE_LIMIT=1000
API_RETRY_ATTEMPTS=3
```

### Personalización de Comportamiento

- **Archivo de configuración personalizado**: Cambiar ruta en `process_repositories.py`
- **Workspace por defecto**: Modificar en `test_connection.py`
- **Límites de paginación**: Ajustar en métodos de `BitbucketClient`
- **Timeouts personalizados**: Configurar en archivo `.env`

---

## 📚 Referencias

### Documentación de la API

- [Bitbucket REST API v2.0](https://developer.atlassian.com/cloud/bitbucket/rest/)
- [Endpoints de Repositorios](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/)
- [Endpoints de Workspaces](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-workspaces/)

### Tecnologías Utilizadas

- **Python 3.13.7**: Lenguaje de programación
- **SQLAlchemy 2.0.43**: ORM para base de datos
- **PostgreSQL 16.10.1**: Base de datos
- **httpx**: Cliente HTTP asíncrono
- **Pydantic**: Validación de datos y configuración

### Estándares y Mejores Prácticas

- **PEP 8**: Guía de estilo de código Python
- **AsyncIO**: Programación asíncrona para mejor rendimiento
- **Repository Pattern**: Patrón de acceso a datos
- **Dependency Injection**: Inyección de dependencias para testing

---

## 📞 Soporte y Mantenimiento

### Monitoreo Continuo

- Verificar logs regularmente para detectar patrones de error
- Monitorear uso de la API para evitar exceder límites
- Revisar estadísticas de procesamiento para optimizaciones

### Actualizaciones

- Mantener dependencias actualizadas
- Revisar cambios en la API de Bitbucket
- Actualizar configuración según necesidades del negocio

### Troubleshooting

- Usar `test_connection.py` para diagnóstico
- Revisar archivos de log para errores específicos
- Verificar configuración de red y firewall
- Validar credenciales y permisos de API

---

## 📊 Resumen de Funcionalidades Implementadas

### Funcionalidades Principales

| Funcionalidad                     | Script                            | Descripción                                   | Configuración                      |
| --------------------------------- | --------------------------------- | --------------------------------------------- | ---------------------------------- |
| **Prueba de Conexión**            | `test_connection.py`              | Verifica conectividad con Bitbucket           | Variables de entorno               |
| **Procesamiento de Repositorios** | `process_repositories.py`         | Procesa repositorios específicos              | `config/repositories.json`         |
| **Proyectos del Workspace**       | `process_workspace_projects.py`   | Procesa todos los proyectos del workspace     | Workspace configurado              |
| **Proyectos Configurados**        | `process_config_projects.py`      | Procesa proyectos específicos                 | `config/projects.json`             |
| **Repositorios del Proyecto**     | `process_project_repositories.py` | Procesa todos los repositorios de un proyecto | `config/project_repositories.json` |

### Características Comunes

- ✅ **Progreso visual**: Todos los scripts muestran porcentaje de procesamiento
- ✅ **Validación por UUID**: Evita duplicados y actualiza registros existentes
- ✅ **Manejo de errores robusto**: Continúa procesando aunque algunos elementos fallen
- ✅ **Estadísticas detalladas**: Muestra resumen completo al finalizar
- ✅ **Logging completo**: Registra todas las operaciones para auditoría
- ✅ **Rate limiting**: Respeta los límites de la API de Bitbucket
