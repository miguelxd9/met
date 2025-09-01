# Diccionario de Datos - Sistema de Métricas DevOps

## 📋 Descripción General

Este documento describe la estructura completa de la base de datos `devops_metrics` que integra datos de **Bitbucket** y **SonarCloud** para proporcionar métricas unificadas de desarrollo y calidad de código.

## 🏗️ Arquitectura de la Base de Datos

### **Esquema General:**

```
devops_metrics
├── 📁 Bitbucket Tables (6 tablas)
│   ├── workspaces
│   ├── projects
│   ├── repositories
│   ├── commits
│   ├── pull_requests
│   └── branches
└── 📁 SonarCloud Tables (6 tablas)
    ├── organizations
    ├── sonarcloud_projects
    ├── issues
    ├── security_hotspots
    ├── quality_gates
    └── metrics
```

### **Relaciones Principales:**

- **Workspace** → **Projects** → **Repositories**
- **Repositories** ↔ **SonarCloud Projects** (vinculación bidireccional)
- **SonarCloud Projects** → **Issues, Security Hotspots, Quality Gates, Metrics**

---

## 📊 TABLAS DE BITBUCKET

### **1. 🏢 Tabla: `workspaces`**

**Descripción:** Representa los espacios de trabajo de Bitbucket (equipos/organizaciones)

| Campo          | Tipo     | Longitud | Nullable | Default        | Descripción                           |
| -------------- | -------- | -------- | -------- | -------------- | ------------------------------------- |
| `id`           | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno           |
| `uuid`         | VARCHAR  | 36       | ❌       | -              | UUID único del workspace en Bitbucket |
| `slug`         | VARCHAR  | 100      | ❌       | -              | Identificador legible del workspace   |
| `name`         | VARCHAR  | 200      | ❌       | -              | Nombre del workspace                  |
| `is_private`   | BOOLEAN  | -        | ❌       | FALSE          | Indica si el workspace es privado     |
| `description`  | TEXT     | -        | ✅       | NULL           | Descripción del workspace             |
| `bitbucket_id` | VARCHAR  | 100      | ❌       | -              | ID del workspace en Bitbucket         |
| `website`      | VARCHAR  | 500      | ✅       | NULL           | URL del sitio web del workspace       |
| `location`     | VARCHAR  | 255      | ✅       | NULL           | Ubicación física del workspace        |
| `created_at`   | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro        |
| `updated_at`   | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización         |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `uuid`, `slug`, `bitbucket_id`

**Ejemplo de Datos:**

```sql
INSERT INTO workspaces (uuid, slug, name, is_private, bitbucket_id)
VALUES ('123e4567-e89b-12d3-a456-426614174000', 'ibkteam', 'Interbank Team', false, 'ibkteam');
```

---

### **2. 🎯 Tabla: `projects`**

**Descripción:** Representa los proyectos dentro de un workspace de Bitbucket

| Campo          | Tipo     | Longitud | Nullable | Default        | Descripción                          |
| -------------- | -------- | -------- | -------- | -------------- | ------------------------------------ |
| `id`           | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno          |
| `uuid`         | VARCHAR  | 36       | ❌       | -              | UUID único del proyecto en Bitbucket |
| `key`          | VARCHAR  | 20       | ❌       | -              | Clave del proyecto (ej: 'MMP-PLIN')  |
| `name`         | VARCHAR  | 200      | ❌       | -              | Nombre del proyecto                  |
| `description`  | TEXT     | -        | ✅       | NULL           | Descripción del proyecto             |
| `is_private`   | BOOLEAN  | -        | ❌       | FALSE          | Indica si el proyecto es privado     |
| `bitbucket_id` | VARCHAR  | 100      | ❌       | -              | ID del proyecto en Bitbucket         |
| `avatar_url`   | VARCHAR  | 500      | ✅       | NULL           | URL del avatar del proyecto          |
| `workspace_id` | INTEGER  | -        | ❌       | -              | Referencia al workspace padre        |
| `created_at`   | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro       |
| `updated_at`   | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización        |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `uuid`, `key`, `bitbucket_id`
- **Foreign Key:** `workspace_id` → `workspaces.id`

**Ejemplo de Datos:**

```sql
INSERT INTO projects (uuid, key, name, is_private, bitbucket_id, workspace_id)
VALUES ('456e7890-e89b-12d3-a456-426614174001', 'MMP-PLIN', 'MMP PLIN Project', false, 'mmp-plin', 1);
```

---

### **3. 📚 Tabla: `repositories`**

**Descripción:** Representa los repositorios de código dentro de un proyecto

| Campo          | Tipo     | Longitud | Nullable | Default        | Descripción                             |
| -------------- | -------- | -------- | -------- | -------------- | --------------------------------------- |
| `id`           | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno             |
| `uuid`         | VARCHAR  | 50       | ❌       | -              | UUID único del repositorio en Bitbucket |
| `slug`         | VARCHAR  | 100      | ❌       | -              | Identificador legible del repositorio   |
| `name`         | VARCHAR  | 255      | ❌       | -              | Nombre del repositorio                  |
| `description`  | TEXT     | -        | ✅       | NULL           | Descripción del repositorio             |
| `is_private`   | BOOLEAN  | -        | ❌       | TRUE           | Indica si el repositorio es privado     |
| `language`     | VARCHAR  | 50       | ✅       | NULL           | Lenguaje de programación principal      |
| `bitbucket_id` | VARCHAR  | 100      | ✅       | NULL           | ID del repositorio en Bitbucket         |
| `avatar_url`   | VARCHAR  | 500      | ✅       | NULL           | URL del avatar del repositorio          |
| `website`      | VARCHAR  | 500      | ✅       | NULL           | URL del sitio web del repositorio       |
| `size_bytes`   | BIGINT   | -        | ❌       | 0              | Tamaño del repositorio en bytes         |
| `workspace_id` | INTEGER  | -        | ❌       | -              | Referencia al workspace padre           |
| `project_id`   | INTEGER  | -        | ✅       | NULL           | Referencia al proyecto padre            |
| `created_at`   | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro          |
| `updated_at`   | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización           |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `uuid`, `slug`, `bitbucket_id`
- **Foreign Key:** `workspace_id` → `workspaces.id`
- **Foreign Key:** `project_id` → `projects.id`

**Ejemplo de Datos:**

```sql
INSERT INTO repositories (uuid, slug, name, is_private, language, bitbucket_id, workspace_id, project_id)
VALUES ('789e0123-e89b-12d3-a456-426614174002', 'mmp-plin-api', 'MMP PLIN API', true, 'Java', 'mmp-plin-api', 1, 1);
```

---

### **4. 🔀 Tabla: `commits`**

**Descripción:** Representa los commits realizados en los repositorios

| Campo             | Tipo     | Longitud | Nullable | Default        | Descripción                     |
| ----------------- | -------- | -------- | -------- | -------------- | ------------------------------- |
| `id`              | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno     |
| `hash`            | VARCHAR  | 40       | ❌       | -              | Hash SHA-1 del commit           |
| `bitbucket_id`    | VARCHAR  | 100      | ❌       | -              | ID del commit en Bitbucket      |
| `message`         | TEXT     | -        | ❌       | -              | Mensaje del commit              |
| `author_name`     | VARCHAR  | 200      | ✅       | NULL           | Nombre del autor del commit     |
| `author_email`    | VARCHAR  | 200      | ✅       | NULL           | Email del autor del commit      |
| `commit_date`     | DATETIME | -        | ❌       | -              | Fecha del commit (con timezone) |
| `author_date`     | DATETIME | -        | ❌       | -              | Fecha del autor (con timezone)  |
| `is_merge_commit` | BOOLEAN  | -        | ❌       | FALSE          | Indica si es un commit de merge |
| `repository_id`   | INTEGER  | -        | ❌       | -              | Referencia al repositorio       |
| `created_at`      | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro  |
| `updated_at`      | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización   |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `hash`, `bitbucket_id`
- **Foreign Key:** `repository_id` → `repositories.id`

**Ejemplo de Datos:**

```sql
INSERT INTO commits (hash, bitbucket_id, message, author_name, author_email, commit_date, author_date, is_merge_commit, repository_id)
VALUES ('a1b2c3d4e5f6...', 'commit-123', 'feat: add new API endpoint', 'John Doe', 'john@interbank.com', '2024-01-15 10:30:00', '2024-01-15 10:30:00', false, 1);
```

---

### **5. 🔀 Tabla: `pull_requests`**

**Descripción:** Representa los pull requests en los repositorios

| Campo           | Tipo     | Longitud | Nullable | Default        | Descripción                                  |
| --------------- | -------- | -------- | -------- | -------------- | -------------------------------------------- |
| `id`            | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno                  |
| `bitbucket_id`  | VARCHAR  | 100      | ❌       | -              | ID del pull request en Bitbucket             |
| `title`         | VARCHAR  | 500      | ❌       | -              | Título del pull request                      |
| `description`   | TEXT     | -        | ✅       | NULL           | Descripción del pull request                 |
| `state`         | VARCHAR  | 20       | ❌       | -              | Estado: OPEN, MERGED, DECLINED               |
| `author_name`   | VARCHAR  | 200      | ✅       | NULL           | Nombre del autor                             |
| `author_email`  | VARCHAR  | 200      | ✅       | NULL           | Email del autor                              |
| `source_branch` | VARCHAR  | 100      | ❌       | -              | Rama de origen                               |
| `target_branch` | VARCHAR  | 100      | ❌       | -              | Rama de destino                              |
| `created_date`  | DATETIME | -        | ❌       | -              | Fecha de creación (con timezone)             |
| `updated_date`  | DATETIME | -        | ❌       | -              | Fecha de última actualización (con timezone) |
| `closed_date`   | DATETIME | -        | ✅       | NULL           | Fecha de cierre (con timezone)               |
| `merged_date`   | DATETIME | -        | ✅       | NULL           | Fecha de merge (con timezone)                |
| `repository_id` | INTEGER  | -        | ❌       | -              | Referencia al repositorio                    |
| `created_at`    | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro               |
| `updated_at`    | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización                |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `bitbucket_id`
- **Foreign Key:** `repository_id` → `repositories.id`

**Ejemplo de Datos:**

```sql
INSERT INTO pull_requests (bitbucket_id, title, description, state, author_name, source_branch, target_branch, created_date, repository_id)
VALUES ('pr-456', 'Add user authentication', 'Implement OAuth2 authentication', 'OPEN', 'Jane Smith', 'feature/auth', 'main', '2024-01-15 14:00:00', 1);
```

---

### **6. 🌿 Tabla: `branches`**

**Descripción:** Representa las ramas en los repositorios

| Campo           | Tipo     | Longitud | Nullable | Default        | Descripción                    |
| --------------- | -------- | -------- | -------- | -------------- | ------------------------------ |
| `id`            | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno    |
| `name`          | VARCHAR  | 100      | ❌       | -              | Nombre de la rama              |
| `type`          | VARCHAR  | 20       | ❌       | -              | Tipo: BRANCH, PULL_REQUEST     |
| `target_hash`   | VARCHAR  | 40       | ❌       | -              | Hash del commit objetivo       |
| `repository_id` | INTEGER  | -        | ❌       | -              | Referencia al repositorio      |
| `created_at`    | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro |
| `updated_at`    | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización  |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `name` + `repository_id` (composite)
- **Foreign Key:** `repository_id` → `repositories.id`

**Ejemplo de Datos:**

```sql
INSERT INTO branches (name, type, target_hash, repository_id)
VALUES ('main', 'BRANCH', 'a1b2c3d4e5f6...', 1);
```

---

## ☁️ TABLAS DE SONARCLOUD

### **1. 🏢 Tabla: `organizations`**

**Descripción:** Representa las organizaciones en SonarCloud

| Campo           | Tipo     | Longitud | Nullable | Default        | Descripción                         |
| --------------- | -------- | -------- | -------- | -------------- | ----------------------------------- |
| `id`            | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno         |
| `key`           | VARCHAR  | 100      | ❌       | -              | Clave única de la organización      |
| `name`          | VARCHAR  | 255      | ❌       | -              | Nombre de la organización           |
| `description`   | TEXT     | -        | ✅       | NULL           | Descripción de la organización      |
| `url`           | VARCHAR  | 500      | ✅       | NULL           | URL de la organización              |
| `sonarcloud_id` | VARCHAR  | 100      | ✅       | NULL           | ID de la organización en SonarCloud |
| `avatar_url`    | VARCHAR  | 500      | ✅       | NULL           | URL del avatar de la organización   |
| `created_at`    | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro      |
| `updated_at`    | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización       |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `key`, `sonarcloud_id`

**Ejemplo de Datos:**

```sql
INSERT INTO organizations (key, name, description, url)
VALUES ('interbank', 'Interbank', 'Organización principal de Interbank', 'https://sonarcloud.io/organizations/interbank');
```

---

### **2. 🎯 Tabla: `sonarcloud_projects`**

**Descripción:** Representa los proyectos en SonarCloud y su vinculación con Bitbucket

| Campo                     | Tipo     | Longitud | Nullable | Default        | Descripción                                  |
| ------------------------- | -------- | -------- | -------- | -------------- | -------------------------------------------- |
| `id`                      | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno                  |
| `key`                     | VARCHAR  | 100      | ❌       | -              | Clave única del proyecto en SonarCloud       |
| `name`                    | VARCHAR  | 255      | ❌       | -              | Nombre del proyecto                          |
| `description`             | TEXT     | -        | ✅       | NULL           | Descripción del proyecto                     |
| `visibility`              | VARCHAR  | 50       | ✅       | NULL           | Visibilidad: public, private                 |
| `sonarcloud_id`           | VARCHAR  | 100      | ✅       | NULL           | ID del proyecto en SonarCloud                |
| `qualifier`               | VARCHAR  | 50       | ✅       | NULL           | Tipo: TRK, APP, VW, DEV                      |
| `scm_url`                 | VARCHAR  | 500      | ✅       | NULL           | URL del repositorio SCM                      |
| `scm_provider`            | VARCHAR  | 50       | ✅       | NULL           | Proveedor SCM: git, svn                      |
| `last_analysis_date`      | DATETIME | -        | ✅       | NULL           | Fecha del último análisis                    |
| `revision`                | VARCHAR  | 100      | ✅       | NULL           | Revisión del proyecto                        |
| `organization_id`         | INTEGER  | -        | ❌       | -              | Referencia a la organización                 |
| `bitbucket_repository_id` | INTEGER  | -        | ✅       | NULL           | **VINCULACIÓN** con repositorio de Bitbucket |
| `created_at`              | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro               |
| `updated_at`              | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización                |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `key`, `sonarcloud_id`
- **Foreign Key:** `organization_id` → `organizations.id`
- **Foreign Key:** `bitbucket_repository_id` → `repositories.id`

**Ejemplo de Datos:**

```sql
INSERT INTO sonarcloud_projects (key, name, qualifier, organization_id, bitbucket_repository_id)
VALUES ('aad-pe.interbank.channel.aad.aaddigitaluserlock:aad-digital-user-lock', 'AAD Digital User Lock', 'TRK', 1, 1);
```

---

### **3. ⚠️ Tabla: `issues`**

**Descripción:** Representa los problemas de calidad del código detectados por SonarCloud

| Campo                   | Tipo     | Longitud | Nullable | Default        | Descripción                                     |
| ----------------------- | -------- | -------- | -------- | -------------- | ----------------------------------------------- |
| `id`                    | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno                     |
| `sonarcloud_id`         | VARCHAR  | 100      | ❌       | -              | ID del issue en SonarCloud                      |
| `key`                   | VARCHAR  | 100      | ❌       | -              | Clave única del issue                           |
| `rule`                  | VARCHAR  | 100      | ❌       | -              | Regla que generó el issue                       |
| `severity`              | ENUM     | -        | ❌       | -              | **BLOCKER, CRITICAL, MAJOR, MINOR, INFO**       |
| `type`                  | ENUM     | -        | ❌       | -              | **BUG, VULNERABILITY, CODE_SMELL**              |
| `status`                | ENUM     | -        | ❌       | -              | **OPEN, CONFIRMED, REOPENED, RESOLVED, CLOSED** |
| `component`             | VARCHAR  | 500      | ✅       | NULL           | Componente afectado                             |
| `line`                  | INTEGER  | -        | ✅       | NULL           | Línea del código                                |
| `start_line`            | INTEGER  | -        | ✅       | NULL           | Línea de inicio                                 |
| `end_line`              | INTEGER  | -        | ✅       | NULL           | Línea de fin                                    |
| `start_offset`          | INTEGER  | -        | ✅       | NULL           | Offset de inicio                                |
| `end_offset`            | INTEGER  | -        | ✅       | NULL           | Offset de fin                                   |
| `message`               | TEXT     | -        | ❌       | -              | Mensaje descriptivo del issue                   |
| `effort`                | VARCHAR  | 50       | ✅       | NULL           | Esfuerzo estimado para resolver                 |
| `debt`                  | VARCHAR  | 50       | ✅       | NULL           | Deuda técnica                                   |
| `creation_date`         | DATETIME | -        | ✅       | NULL           | Fecha de creación del issue                     |
| `update_date`           | DATETIME | -        | ✅       | NULL           | Fecha de última actualización                   |
| `close_date`            | DATETIME | -        | ✅       | NULL           | Fecha de cierre                                 |
| `author`                | VARCHAR  | 200      | ✅       | NULL           | Autor del código                                |
| `assignee`              | VARCHAR  | 200      | ✅       | NULL           | Asignado para resolver                          |
| `sonarcloud_project_id` | INTEGER  | -        | ❌       | -              | Referencia al proyecto de SonarCloud            |
| `created_at`            | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro                  |
| `updated_at`            | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización                   |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `key`, `sonarcloud_id`
- **Foreign Key:** `sonarcloud_project_id` → `sonarcloud_projects.id`

**Enums:**

```sql
-- Severity
CREATE TYPE issueseverity AS ENUM ('BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO');

-- Type
CREATE TYPE issuetype AS ENUM ('BUG', 'VULNERABILITY', 'CODE_SMELL');

-- Status
CREATE TYPE issuestatus AS ENUM ('OPEN', 'CONFIRMED', 'REOPENED', 'RESOLVED', 'CLOSED');
```

**Ejemplo de Datos:**

```sql
INSERT INTO issues (sonarcloud_id, key, rule, severity, type, status, message, sonarcloud_project_id)
VALUES ('AXeF8HqJ9K2L3M4N5O6P7', 'issue-123', 'java:S1066', 'MAJOR', 'CODE_SMELL', 'OPEN', 'Merge this if statement with the enclosing one', 1);
```

---

### **4. 🔒 Tabla: `security_hotspots`**

**Descripción:** Representa los puntos críticos de seguridad detectados por SonarCloud

| Campo                   | Tipo     | Longitud | Nullable | Default        | Descripción                          |
| ----------------------- | -------- | -------- | -------- | -------------- | ------------------------------------ |
| `id`                    | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno          |
| `sonarcloud_id`         | VARCHAR  | 100      | ❌       | -              | ID del hotspot en SonarCloud         |
| `key`                   | VARCHAR  | 100      | ❌       | -              | Clave única del hotspot              |
| `rule`                  | VARCHAR  | 100      | ❌       | -              | Regla que generó el hotspot          |
| `status`                | ENUM     | -        | ❌       | -              | **TO_REVIEW, IN_REVIEW, REVIEWED**   |
| `resolution`            | ENUM     | -        | ✅       | NULL           | **SAFE, ACKNOWLEDGED, FIXED**        |
| `component`             | VARCHAR  | 500      | ✅       | NULL           | Componente afectado                  |
| `line`                  | INTEGER  | -        | ✅       | NULL           | Línea del código                     |
| `start_line`            | INTEGER  | -        | ✅       | NULL           | Línea de inicio                      |
| `end_line`              | INTEGER  | -        | ✅       | NULL           | Línea de fin                         |
| `start_offset`          | INTEGER  | -        | ✅       | NULL           | Offset de inicio                     |
| `end_offset`            | INTEGER  | -        | ✅       | NULL           | Offset de fin                        |
| `message`               | TEXT     | -        | ❌       | -              | Mensaje descriptivo del hotspot      |
| `effort`                | VARCHAR  | 50       | ✅       | NULL           | Esfuerzo estimado para resolver      |
| `debt`                  | VARCHAR  | 50       | ✅       | NULL           | Deuda técnica                        |
| `creation_date`         | DATETIME | -        | ✅       | NULL           | Fecha de creación del hotspot        |
| `update_date`           | DATETIME | -        | ✅       | NULL           | Fecha de última actualización        |
| `author`                | VARCHAR  | 200      | ✅       | NULL           | Autor del código                     |
| `assignee`              | VARCHAR  | 200      | ✅       | NULL           | Asignado para revisar                |
| `sonarcloud_project_id` | INTEGER  | -        | ❌       | -              | Referencia al proyecto de SonarCloud |
| `created_at`            | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro       |
| `updated_at`            | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización        |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `key`, `sonarcloud_id`
- **Foreign Key:** `sonarcloud_project_id` → `sonarcloud_projects.id`

**Enums:**

```sql
-- Status
CREATE TYPE securityhotspotstatus AS ENUM ('TO_REVIEW', 'IN_REVIEW', 'REVIEWED');

-- Resolution
CREATE TYPE securityhotspotresolution AS ENUM ('SAFE', 'ACKNOWLEDGED', 'FIXED');
```

**Ejemplo de Datos:**

```sql
INSERT INTO security_hotspots (sonarcloud_id, key, rule, status, message, sonarcloud_project_id)
VALUES ('BXeF8HqJ9K2L3M4N5O6P8', 'hotspot-456', 'java:S5146', 'TO_REVIEW', 'Make sure this HTTP request is not used to download untrusted files', 1);
```

---

### **5. 🚦 Tabla: `quality_gates`**

**Descripción:** Representa los estados de las puertas de calidad de los proyectos

| Campo                      | Tipo     | Longitud | Nullable | Default        | Descripción                          |
| -------------------------- | -------- | -------- | -------- | -------------- | ------------------------------------ |
| `id`                       | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno          |
| `sonarcloud_id`            | VARCHAR  | 100      | ❌       | -              | ID del quality gate en SonarCloud    |
| `key`                      | VARCHAR  | 100      | ❌       | -              | Clave única del quality gate         |
| `name`                     | VARCHAR  | 255      | ❌       | -              | Nombre del quality gate              |
| `status`                   | ENUM     | -        | ❌       | -              | **OK, WARN, ERROR**                  |
| `conditions_count`         | INTEGER  | -        | ✅       | NULL           | Número de condiciones                |
| `ignored_conditions_count` | INTEGER  | -        | ✅       | NULL           | Número de condiciones ignoradas      |
| `analysis_date`            | DATETIME | -        | ✅       | NULL           | Fecha del análisis                   |
| `sonarcloud_project_id`    | INTEGER  | -        | ❌       | -              | Referencia al proyecto de SonarCloud |
| `created_at`               | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro       |
| `updated_at`               | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización        |

**Constraints:**

- **Primary Key:** `id`
- **Unique:** `key`, `sonarcloud_id`
- **Foreign Key:** `sonarcloud_project_id` → `sonarcloud_projects.id`

**Enums:**

```sql
-- Status
CREATE TYPE qualitygatestatus AS ENUM ('OK', 'WARN', 'ERROR');
```

**Ejemplo de Datos:**

```sql
INSERT INTO quality_gates (sonarcloud_id, key, name, status, conditions_count, sonarcloud_project_id)
VALUES ('CXeF8HqJ9K2L3M4N5O6P9', 'qg-789', 'SonarCloud Quality Gate', 'OK', 5, 1);
```

---

### **6. 📊 Tabla: `metrics`**

**Descripción:** Representa las métricas de calidad y rendimiento de los proyectos

| Campo                   | Tipo     | Longitud | Nullable | Default        | Descripción                                     |
| ----------------------- | -------- | -------- | -------- | -------------- | ----------------------------------------------- |
| `id`                    | INTEGER  | -        | ❌       | AUTO_INCREMENT | Identificador único interno                     |
| `key`                   | VARCHAR  | 100      | ❌       | -              | Clave de la métrica                             |
| `name`                  | VARCHAR  | 255      | ❌       | -              | Nombre de la métrica                            |
| `value`                 | FLOAT    | -        | ✅       | NULL           | Valor numérico de la métrica                    |
| `formatted_value`       | VARCHAR  | 100      | ✅       | NULL           | Valor formateado (ej: "1.5k")                   |
| `type`                  | VARCHAR  | 50       | ✅       | NULL           | Tipo de métrica                                 |
| `domain`                | VARCHAR  | 50       | ✅       | NULL           | Dominio: Reliability, Security, Maintainability |
| `analysis_date`         | DATETIME | -        | ✅       | NULL           | Fecha del análisis                              |
| `sonarcloud_project_id` | INTEGER  | -        | ❌       | -              | Referencia al proyecto de SonarCloud            |
| `created_at`            | DATETIME | -        | ❌       | GETDATE()      | Fecha de creación del registro                  |
| `updated_at`            | DATETIME | -        | ❌       | GETDATE()      | Fecha de última actualización                   |

**Constraints:**

- **Primary Key:** `id`
- **Foreign Key:** `sonarcloud_project_id` → `sonarcloud_projects.id`

**Ejemplo de Datos:**

```sql
INSERT INTO metrics (key, name, value, formatted_value, type, domain, sonarcloud_project_id)
VALUES ('bugs', 'Bugs', 2.0, '2', 'INT', 'Reliability', 1);
```

---

## 🔗 RELACIONES Y VINCULACIONES

### **Diagrama de Relaciones:**

```
workspaces (1) ←→ (N) projects (1) ←→ (N) repositories (1) ←→ (N) commits
                                                                    ↓
                                                              (1) ←→ (N) pull_requests
                                                                    ↓
                                                              (1) ←→ (N) branches

organizations (1) ←→ (N) sonarcloud_projects (1) ←→ (N) issues
                                              ↓
                                        (1) ←→ (N) security_hotspots
                                              ↓
                                        (1) ←→ (N) quality_gates
                                              ↓
                                        (1) ←→ (N) metrics

repositories (1) ←→ (1) sonarcloud_projects  ←→ (N) [issues, security_hotspots, quality_gates, metrics]
```

### **Vinculación Bitbucket ↔ SonarCloud:**

La tabla `sonarcloud_projects` contiene el campo `bitbucket_repository_id` que establece la relación bidireccional entre:

- **Repositorios de Bitbucket** → **Proyectos de SonarCloud**
- **Proyectos de SonarCloud** → **Repositorios de Bitbucket**

### **Flujo de Datos:**

1. **Bitbucket** → Workspaces → Projects → Repositories
2. **SonarCloud** → Organizations → Projects → Quality Metrics
3. **Vinculación** → Repositories ↔ SonarCloud Projects
4. **Métricas Unificadas** → Issues, Security, Quality Gates, Metrics

---

## 📈 ÍNDICES Y OPTIMIZACIÓN

### **Índices Principales:**

```sql
-- Bitbucket
CREATE INDEX ix_workspaces_slug ON workspaces(slug);
CREATE INDEX ix_projects_key ON projects(key);
CREATE INDEX ix_repositories_slug ON repositories(slug);
CREATE INDEX ix_commits_hash ON commits(hash);
CREATE INDEX ix_pull_requests_state ON pull_requests(state);

-- SonarCloud
CREATE INDEX ix_sonarcloud_projects_key ON sonarcloud_projects(key);
CREATE INDEX ix_sonarcloud_projects_organization_id ON sonarcloud_projects(organization_id);
CREATE INDEX ix_issues_severity ON issues(severity);
CREATE INDEX ix_issues_status ON issues(status);
CREATE INDEX ix_metrics_key ON metrics(key);
```

### **Optimizaciones de Consulta:**

- **JOINs optimizados** entre tablas relacionadas
- **Índices compuestos** para consultas frecuentes
- **Particionamiento** por fecha para tablas grandes
- **Caché** de métricas calculadas

---

## 🔍 CONSULTAS DE EJEMPLO

### **1. Proyectos con Métricas de Calidad:**

```sql
SELECT
    p.key as project_key,
    p.name as project_name,
    r.slug as repository_slug,
    scp.key as sonarcloud_key,
    qg.status as quality_gate_status,
    COUNT(i.id) as total_issues,
    COUNT(CASE WHEN i.severity = 'BLOCKER' THEN 1 END) as blocker_issues
FROM projects p
JOIN repositories r ON p.id = r.project_id
JOIN sonarcloud_projects scp ON r.id = scp.bitbucket_repository_id
LEFT JOIN quality_gates qg ON scp.id = qg.sonarcloud_project_id
LEFT JOIN issues i ON scp.id = i.sonarcloud_project_id
GROUP BY p.id, p.key, p.name, r.slug, scp.key, qg.status;
```

### **2. Métricas de Seguridad por Proyecto:**

```sql
SELECT
    p.name as project_name,
    COUNT(sh.id) as security_hotspots,
    COUNT(CASE WHEN sh.status = 'TO_REVIEW' THEN 1 END) as pending_review,
    COUNT(CASE WHEN sh.resolution = 'FIXED' THEN 1 END) as fixed_hotspots
FROM projects p
JOIN repositories r ON p.id = r.project_id
JOIN sonarcloud_projects scp ON r.id = scp.bitbucket_repository_id
LEFT JOIN security_hotspots sh ON scp.id = sh.sonarcloud_project_id
GROUP BY p.id, p.name;
```

### **3. Evolución de Issues por Fecha:**

```sql
SELECT
    DATE(i.creation_date) as issue_date,
    COUNT(i.id) as new_issues,
    COUNT(CASE WHEN i.status = 'RESOLVED' THEN 1 END) as resolved_issues
FROM issues i
JOIN sonarcloud_projects scp ON i.sonarcloud_project_id = scp.id
WHERE i.creation_date >= DATEADD(day, -30, GETDATE())
GROUP BY DATE(i.creation_date)
ORDER BY issue_date;
```

---

## 📊 MÉTRICAS CALCULADAS

### **Métricas de Calidad:**

- **Reliability Rating**: Basado en bugs
- **Security Rating**: Basado en vulnerabilities y security hotspots
- **Maintainability Rating**: Basado en code smells
- **Coverage**: Porcentaje de código cubierto por tests
- **Duplications**: Código duplicado

### **Métricas de Desarrollo:**

- **Commit Frequency**: Frecuencia de commits
- **Pull Request Velocity**: Velocidad de merge de PRs
- **Code Churn**: Cambios en el código
- **Technical Debt**: Deuda técnica acumulada

---

## 🚀 CONSIDERACIONES DE IMPLEMENTACIÓN

### **1. Escalabilidad:**

- **Particionamiento** de tablas grandes por fecha
- **Archivado** de datos históricos
- **Compresión** de datos antiguos

### **2. Rendimiento:**

- **Índices estratégicos** para consultas frecuentes
- **Métricas pre-calculadas** para dashboards
- **Caché** de consultas complejas

### **3. Mantenimiento:**

- **Limpieza automática** de datos obsoletos
- **Backup incremental** de datos críticos
- **Monitoreo** de rendimiento de consultas

---

## 📝 NOTAS IMPORTANTES

1. **Todas las fechas** se almacenan en UTC para consistencia
2. **Los campos de vinculación** permiten NULL para flexibilidad
3. **Los enums** están estandarizados según las APIs de SonarCloud
4. **Los índices** están optimizados para consultas de reporting
5. **La estructura** permite escalabilidad horizontal y vertical

---

**Versión del Documento:** 1.0  
**Última Actualización:** Enero 2024  
**Mantenido por:** Equipo de DevOps
