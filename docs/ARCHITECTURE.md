# Arquitectura del Sistema - Gestión Comercial

Este documento describe la arquitectura técnica, los componentes clave, los flujos de autenticación y la estrategia de base de datos del backend de **Gestión Comercial**.

---

## 1. Visión General de la Arquitectura

El sistema está construido sobre **Django 6.1** y estructurado para entornos desacoplados (Backend API REST + Frontend), con soporte híbrido de base de datos y autenticación corporativa contra **Active Directory (AD / LDAP)**.

```mermaid
graph TD
    Client["Cliente / Frontend Web"] -->|"HTTP / REST API"| DjangoBackend["Django 6.1 Backend (core)"]
    
    subgraph "Autenticación"
        DjangoBackend -->|"1. Intento AD"| ADBackend["ActiveDirectoryBackend (ldap3)"]
        ADBackend -->|"LDAP / LDAPS"| DomainController["Controlador de Dominio (AD)"]
        DjangoBackend -->|"2. Fallback local"| ModelBackend["Django ModelBackend"]
    end

    subgraph "Persistencia de Datos"
        DjangoBackend -->|"PRODUCTION=False"| SQLite["SQLite (db.sqlite3)"]
        DjangoBackend -->|"PRODUCTION=True"| PostgreSQL["PostgreSQL (psycopg 3)"]
    end

    subgraph "Modelos de Usuario"
        DjangoBackend --> DjangoUser["auth.User (Django Core)"]
        DjangoUser <-->|"OneToOneField"| UserProfile["Dashboard.UserProfile (Perfil AD)"]
    end
```

---

## 2. Pila Tecnológica (Tech Stack)

| Componente | Tecnología | Versión | Propósito |
| :--- | :--- | :--- | :--- |
| **Framework Web** | Django | 6.1.1 | Núcleo del backend y ORM |
| **Gestión de Entornos** | django-environ | 0.14.0 | Carga de variables tipadas desde `.env` |
| **Directorio Activo / LDAP** | ldap3 | 2.9.1 | Conexión 100% pura Python con Active Directory |
| **Driver PostgreSQL** | psycopg (binary) | 3.3.6 | Driver moderno de alta velocidad para producción |
| **Base de Datos Local** | SQLite | 3.x | Base de datos ligera para desarrollo rápido |
| **Base de Datos Producción** | PostgreSQL | 14+ | Motor relacional robusto con connection pooling |

---

## 3. Estrategia Dinámica de Base de Datos

El sistema conmuta de forma automática entre motores según la variable de entorno `PRODUCTION`:

```python
if PRODUCTION:
    # Producción: PostgreSQL con connection pooling
    DATABASES['default'] = env.db('DATABASE_URL', default=default_postgres_url)
    DATABASES['default']['CONN_MAX_AGE'] = env.int('DB_CONN_MAX_AGE', default=600)
else:
    # Desarrollo: SQLite local
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
```

- **Desarrollo (`PRODUCTION=False`):** No requiere instalar ni levantar un servidor de base de datos; crea `db.sqlite3` en `backend/`.
- **Producción (`PRODUCTION=True`):** Se conecta a PostgreSQL mediante `DATABASE_URL` o parámetros individuales (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`). Conexiones persistentes activas (`CONN_MAX_AGE=600`).

---

## 4. Ciclo de Vida de Usuario y Perfil (`UserProfile`)

Para cumplir con el requerimiento de sincronización corporativa, cada usuario tiene asociado un perfil extendido en la app `Dashboard`:

```mermaid
classDiagram
    class User {
        +Integer id
        +String username
        +String first_name
        +String last_name
        +String email
        +Boolean is_staff
        +Boolean is_superuser
        +Boolean is_active
    }

    class UserProfile {
        +Integer id
        +User user (OneToOne)
        +String department
        +String job_title
        +String phone
        +String ad_dn
        +Text ad_groups
        +DateTime created_at
        +DateTime updated_at
    }

    User "1" <--> "1" UserProfile : user.profile
```

### Automatizaciones:
1. **Señal `post_save`:** Cada vez que se crea un `User` (sea por comando, migración o vista), la señal en `Dashboard/signals.py` garantiza que se cree su correspondiente `UserProfile`.
2. **Sincronización AD en inicio de sesión:** Si el usuario proviene de Active Directory, `ActiveDirectoryBackend` extrae sus atributos (`givenName`, `sn`, `mail`, `department`, `title`, `telephoneNumber`, `memberOf`) y actualiza tanto el `User` como el `UserProfile`.
