# 🚀 DevOps Metrics Collection Platform

Plataforma unificada para la recolección y análisis de métricas de calidad de código desde múltiples plataformas DevOps.

## 📊 **Proyectos Incluidos**

### 🔗 **Bitbucket Metrics**
- **Descripción**: Recolección de métricas de repositorios Git en Bitbucket
- **Características**: Pull requests, commits, branches, code review metrics
- **Tecnologías**: Python, PostgreSQL, SQLAlchemy, Alembic
- **Documentación**: [Ver proyecto Bitbucket](./bitbucket/README.md)

### ☁️ **SonarCloud Metrics**
- **Descripción**: Recolección de métricas de calidad de código desde SonarCloud
- **Características**: Coverage, duplications, bugs, vulnerabilities, security hotspots
- **Tecnologías**: Python, PostgreSQL, SQLAlchemy, Alembic, SonarCloud API
- **Documentación**: [Ver proyecto SonarCloud](./sonarcloud/README.md)

## 🏗️ **Arquitectura**

```
┌─────────────────────────────────────────────────────────────┐
│                    DevOps Metrics Platform                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Bitbucket     │    │   SonarCloud    │                │
│  │   Metrics       │    │   Metrics       │                │
│  └─────────────────┘    └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│                    Shared Infrastructure                    │
│  • Database Layer (PostgreSQL)                             │
│  • Configuration Management                                │
│  • Logging & Monitoring                                    │
│  • Common Utilities                                        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 **Inicio Rápido**

### **Prerrequisitos**
- Python 3.8+
- PostgreSQL 12+
- Docker (opcional)

### **Instalación**
```bash
# Clonar el repositorio
git clone <your-repo-url>
cd metricas_coe_devops

# Instalar dependencias comunes
pip install -r requirements.txt

# Configurar base de datos
docker-compose up -d postgres

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### **Uso por Proyecto**

#### **Bitbucket Metrics**
```bash
cd bitbucket
python -m src.scripts.collect_metrics --workspace tu-workspace
```

#### **SonarCloud Metrics**
```bash
cd sonarcloud
python -m src.scripts.collect_metrics --organization tu-org --sync-all
```

## 📁 **Estructura del Repositorio**

```
metricas_coe_devops/
├── README.md                    # Este archivo
├── .gitignore                  # Gitignore global
├── requirements.txt             # Dependencias comunes
├── docker-compose.yml          # Orquestación de servicios
├── .github/                    # GitHub Actions (opcional)
│   └── workflows/
├── bitbucket/                  # Proyecto Bitbucket
│   ├── src/
│   ├── alembic/
│   ├── requirements.txt
│   └── README.md
├── sonarcloud/                 # Proyecto SonarCloud
│   ├── src/
│   ├── alembic/
│   ├── requirements.txt
│   └── README.md
└── shared/                     # Código compartido
    ├── utils/
    ├── config/
    └── database/
```

## 🔧 **Configuración**

### **Variables de Entorno**
```bash
# Base de datos compartida
DATABASE_URL=postgresql://user:pass@localhost:5432/devops_metrics

# Bitbucket
BITBUCKET_USERNAME=tu-usuario
BITBUCKET_APP_PASSWORD=tu-token

# SonarCloud
SONARCLOUD_TOKEN=tu-token
SONARCLOUD_ORGANIZATION=tu-org
```

## 📈 **Métricas Disponibles**

### **Bitbucket**
- Pull Requests (abiertos, cerrados, merged)
- Commits por branch
- Code review metrics
- Branch protection rules
- Repository activity

### **SonarCloud**
- Code coverage
- Duplicated lines
- Code smells, bugs, vulnerabilities
- Security hotspots
- Quality gate status
- Technical debt

## 🤝 **Contribución**

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 **Licencia**

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 **Soporte**

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/metricas_coe_devops/issues)
- **Documentación**: [Wiki del proyecto](https://github.com/tu-usuario/metricas_coe_devops/wiki)
- **Contacto**: tu-email@ejemplo.com

---

**Desarrollado con ❤️ para la comunidad DevOps**
