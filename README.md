# Sistema de Gestión Comercial

Plataforma empresarial de Gestión Comercial desarrollada con **Django 6.1** y arquitectura preparada para Frontend desacoplado (React/Vite), con autenticación corporativa contra **Active Directory (AD / LDAP)**, control de acceso por grupos de seguridad/GPO, conmutador dinámico de base de datos (PostgreSQL/SQLite) y API REST basada en funciones.

---

## 📑 Índice de Documentación

| Documento | Enlace | Descripción |
| :--- | :--- | :--- |
| **Arquitectura del Sistema** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Diagramas de componentes, flujo de datos, tech stack y modelo de datos. |
| **Manual de Active Directory** | [docs/AUTHENTICATION_LDAP.md](docs/AUTHENTICATION_LDAP.md) | Guía de configuración de AD, variables de entorno, control de acceso por grupos/GPO y troubleshooting. |
| **Especificación de API REST** | [docs/API_REST_SPEC.md](docs/API_REST_SPEC.md) | Catálogo de endpoints, contratos de petición/respuesta y plantilla de Vistas Basadas en Funciones (FBVs). |

---

## 🚀 Inicio Rápido en Desarrollo Local

### 1. Requisitos Previos
- Python 3.12+ (o Python 3.14)
- Entorno virtual activado (`venv`)

### 2. Instalación de Dependencias
```bash
pip install -r backend/requirements.txt
```

### 3. Configuración del Archivo `.env`
Copia el archivo de plantilla a `.env` dentro de `backend/`:
```bash
cp backend/.env.example backend/.env
```

Por defecto, en modo local viene configurado con:
- `DEBUG=True`
- `PRODUCTION=False` (Utiliza **SQLite** automáticamente en `backend/db.sqlite3`)
- `LDAP_ENABLED=False` (Usa autenticación local de Django para trabajar sin conexión al Controlador de Dominio)

### 4. Ejecución de Migraciones y Verificación
```bash
python backend/manage.py migrate
python backend/manage.py check
```

### 5. Crear Superusuario Local
```bash
python backend/manage.py createsuperuser
```

### 6. Iniciar Servidor de Desarrollo
```bash
python backend/manage.py runserver
```

El panel de administración estará disponible en: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## ⚙️ Conmutador de Entorno (SQLite vs PostgreSQL)

El sistema conmuta de base de datos dinámicamente mediante la variable `PRODUCTION` en [backend/.env](backend/.env):

- **Desarrollo:** `PRODUCTION=False` -> Utiliza **SQLite**.
- **Producción:** `PRODUCTION=True` -> Utiliza **PostgreSQL** (`psycopg 3`), con soporte para `DATABASE_URL` completa o parámetros individuales (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).

---

## 🌐 Versionado Dinámico de la API REST (`API_PREFIX`)

El prefijo y versión de todos los endpoints de la API se controla desde el `.env`:
```env
API_PREFIX=api/v1/
```
Esto permite actualizar a `api/v2/` en el futuro sin modificar las definiciones de rutas ni los controladores del código fuente. Todos los endpoints quedan montados bajo:
- `http://127.0.0.1:8000/api/v1/auth/login/`
- `http://127.0.0.1:8000/api/v1/auth/logout/`
- `http://127.0.0.1:8000/api/v1/auth/me/`
- `http://127.0.0.1:8000/api/v1/profile/`
- `http://127.0.0.1:8000/api/v1/dashboard/stats/`

---

## 🏢 Autenticación con Active Directory (AD / LDAP)

La integración utiliza la biblioteca pura en Python **`ldap3`** (sin dependencias C de OpenLDAP):
- **Aprovisionamiento Automático:** En el primer inicio de sesión del usuario en AD, se crea automáticamente su `User` y su `UserProfile` con sus datos corporativos (departamento, cargo, teléfono, grupos).
- **Control por Grupos/GPO:** Si defines `LDAP_REQUIRED_GROUPS=GrupoAutorizado`, solo los usuarios que pertenezcan a ese grupo podrán iniciar sesión.
- **Permisos de Staff/Admin:** Mapeo automático de grupos de AD a `is_staff` y `is_superuser`.
- **Fallback Seguro:** Si LDAP está deshabilitado o el servidor de dominio no responde, el sistema permite ingresar con superusuarios locales creados en la base de datos.

---

## 🧪 Ejecución de Pruebas Unitarias

Para ejecutar las pruebas automatizadas del sistema:
```bash
python backend/manage.py test Dashboard
```
