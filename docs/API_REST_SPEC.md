# Especificación de la API REST (Vistas Basadas en Funciones)

Este documento define el diseño arquitectónico, el estándar de codificación y la especificación de endpoints para la construcción de la API REST del backend mediante **Vistas Basadas en Funciones (Function-Based Views - FBVs)**.

---

## 1. Directrices de Codificación para Vistas por Función

Cada endpoint se implementará como una función pura en `backend/Dashboard/views.py` (o módulos dentro de `backend/Dashboard/api/`), garantizando legibilidad, desacoplamiento y control explícito del flujo.

### Estructura Estándar de una Vista en Función:
```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json

@require_http_methods(["POST"])
def nombre_vista_api(request):
    """
    Descripción clara del endpoint, parámetros y respuesta.
    """
    try:
        # 1. Parseo y validación del payload JSON
        data = json.loads(request.body) if request.body else {}
        
        # 2. Validación de campos obligatorios
        if 'campo_requerido' not in data:
            return JsonResponse({
                "success": False,
                "error": "El campo 'campo_requerido' es obligatorio."
            }, status=400)
            
        # 3. Lógica de negocio
        resultado = ejecutar_logica(data)

        # 4. Respuesta exitosa estructurada
        return JsonResponse({
            "success": True,
            "data": resultado
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "El cuerpo de la solicitud no es un JSON válido."
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": "Error interno del servidor.",
            "details": str(e)
        }, status=500)
```

---

## 2. Formato Estándar de Respuestas

Todas las respuestas de la API siguen un formato unificado para facilitar el consumo desde el Frontend (React, Vue, etc.):

### Respuesta Exitosa (`status: 200 / 201`):
```json
{
    "success": true,
    "message": "Operación completada exitosamente.",
    "data": { ... }
}
```

### Respuesta de Error (`status: 400 / 401 / 403 / 404 / 500`):
```json
{
    "success": false,
    "error": "Descripción comprensible del error.",
    "code": "CODIGO_ERROR_OPCIONAL",
    "details": { ... }
}
```

## 3. Versionado Dinámico mediante Variable de Entorno (`API_PREFIX`)

Para evitar problemas en el futuro al publicar nuevas versiones (v2, v3, etc.), el prefijo base de la API está parametrizado en `.env`:

```env
API_PREFIX=api/v1/
```

En `backend/core/urls.py`, las rutas se montan dinámicamente:
```python
path(settings.API_PREFIX, include('Dashboard.urls'))
```

Si el día de mañana se migra a `api/v2/`, basta con cambiar el valor en `.env` sin modificar el código fuente de los endpoints.

---

## 4. Catálogo de Endpoints Diseñados (Prefijo por defecto: `/api/v1/`)

### 4.1. Autenticación y Sesión (`/api/v1/auth/`)

#### A. Inicio de Sesión (Login AD / Local)
- **Ruta:** `/{API_PREFIX}auth/login/` (por defecto: `/api/v1/auth/login/`)
- **Método:** `POST`
- **Autenticación:** Pública (sin sesión previa)
- **Descripción:** Valida credenciales contra Active Directory (o usuario local), comprueba grupos/GPO autorizados, inicializa sesión y retorna el perfil sincronizado.
- **Request Body:**
  ```json
  {
      "username": "carlos.perez",
      "password": "PasswordSecreta123"
  }
  ```
- **Response Exitosa (`200 OK`):**
  ```json
  {
      "success": true,
      "message": "Inicio de sesión exitoso.",
      "data": {
          "user": {
              "id": 1,
              "username": "carlos.perez",
              "first_name": "Carlos",
              "last_name": "Pérez",
              "email": "carlos.perez@empresa.com",
              "is_staff": false,
              "is_superuser": false
          },
          "profile": {
              "department": "Comercial / Ventas",
              "job_title": "Ejecutivo de Cuentas",
              "phone": "+56 9 8765 4321",
              "ad_groups": ["GestionComercial_Usuarios", "Ventas_Chile"]
          },
          "tokens": {
              "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
              "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
              "token_type": "Bearer",
              "expires_in": 3600,
              "expires_at": "2026-10-06T23:20:00Z"
          }
      }
  }
  ```

#### B. Renovación de Tokens JWT (Refresh Token)
- **Ruta:** `/{API_PREFIX}auth/refresh/` (por defecto: `/api/v1/auth/refresh/`)
- **Método:** `POST`
- **Autenticación:** Pública (requiere enviar el `refresh_token` en el body)
- **Request Body:**
  ```json
  {
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Response Exitosa (`200 OK`):**
  ```json
  {
      "success": true,
      "message": "Token de acceso renovado exitosamente.",
      "data": {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "token_type": "Bearer",
          "expires_in": 3600,
          "expires_at": "2026-10-06T23:20:00Z"
      }
  }
  ```

#### C. Cierre de Sesión (Logout)
- **Ruta:** `/{API_PREFIX}auth/logout/` (por defecto: `/api/v1/auth/logout/`)
- **Método:** `POST`
- **Autenticación:** Requerida (`login_required`)
- **Response Exitosa (`200 OK`):**
  ```json
  {
      "success": true,
      "message": "Sesión cerrada correctamente."
  }
  ```

#### C. Estado de Sesión Actual (Me)
- **Ruta:** `/{API_PREFIX}auth/me/` (por defecto: `/api/v1/auth/me/`)
- **Método:** `GET`
- **Autenticación:** Requerida
- **Descripción:** Retorna los datos del usuario logueado en la sesión actual.

---

### 4.2. Gestión de Perfiles (`/api/v1/profile/`)

#### A. Consultar Mi Perfil
- **Ruta:** `/{API_PREFIX}profile/` (por defecto: `/api/v1/profile/`)
- **Método:** `GET`
- **Autenticación:** Requerida
- **Response Exitosa (`200 OK`):**
  ```json
  {
      "success": true,
      "data": {
          "username": "carlos.perez",
          "full_name": "Carlos Pérez",
          "email": "carlos.perez@empresa.com",
          "department": "Comercial / Ventas",
          "job_title": "Ejecutivo de Cuentas",
          "phone": "+56 9 8765 4321",
          "ad_groups": ["GestionComercial_Usuarios", "Ventas_Chile"],
          "updated_at": "2026-10-05T22:00:00Z"
      }
  }
  ```

#### B. Actualizar Datos de Contacto
- **Ruta:** `/{API_PREFIX}profile/` (por defecto: `/api/v1/profile/`)
- **Método:** `PUT` / `PATCH`
- **Autenticación:** Requerida
- **Campos modificables:** `phone` (los campos corporativos de AD como departamento o cargo se mantienen sincronizados por directorio).

---

### 4.3. Métricas y Dashboard (`/api/v1/dashboard/`)

#### A. Resumen de Estadísticas del Dashboard
- **Ruta:** `/{API_PREFIX}dashboard/stats/` (por defecto: `/api/v1/dashboard/stats/`)
- **Método:** `GET`
- **Autenticación:** Requerida
- **Response Exitosa (`200 OK`):**
  ```json
  {
      "success": true,
      "data": {
          "total_usuarios": 15,
          "usuarios_activos": 12,
          "departamentos": [
              {"name": "Ventas", "total": 8},
              {"name": "Operaciones", "total": 4}
          ]
      }
  }
  ```

### 4.4. Catálogo de Aplicativos y Enlaces Externos (`/api/v1/aplicativos/`)

Permite gestionar los accesos directos y enlaces hacia diferentes aplicativos internos y externos (Launchpad). Cada aplicativo cuenta con su nombre, URL de destino, logo (URL o archivo subido), descripción, orden, estado activo y **control de acceso basado en permisos**.

> [!IMPORTANT]
> **Autenticación Obligatoria y Seguridad JWT:**
> **Todas las URLs del módulo de aplicativos requieren obligatoriamente autenticación.** No existe ninguna URL pública ni anónima. Toda solicitud debe incluir un token JWT vigente en el encabezado `Authorization: Bearer <token>`.
> Si el token ha expirado, la API responderá con `401 Unauthorized` (`code: "TOKEN_EXPIRED"`). Si no se suministra el encabezado o es inválido, responderá con `401 Unauthorized` (`code: "UNAUTHORIZED"` o `"INVALID_TOKEN"`).

#### Control de Acceso y Visibilidad:
- Los aplicativos protegidos **solo son visibles en el listado y detalle** si el usuario solicitante cuenta con los permisos necesarios:
  - **Superusuario:** Acceso total e irrestricto a todos los aplicativos.
  - **Permiso Django o Grupo:** Coincidencia con `user.has_perm()` o grupos de Django del usuario.
  - **Active Directory (AD / LDAP):** Coincidencia con los grupos corporativos sincronizados en `user.profile.ad_groups` o departamentos corporativos en `user.profile.department`.

#### A. Listar Aplicativos
- **Ruta:** `/{API_PREFIX}aplicativos/` (por defecto: `/api/v1/aplicativos/`)
- **Método:** `GET`
- **Autenticación:** Obligatoria (`Bearer <token>`)
- **Filtro de Seguridad:** La API evalúa automáticamente los privilegios de la sesión del usuario y **solo devuelve los aplicativos autorizados**.
- **Query Params opcionales:**
  - `activo=true|false`: Filtra por estado de disponibilidad.
  - `search=texto`: Búsqueda por nombre, descripción o URL.
  - `order_by=orden|-orden|nombre|-nombre|created_at`: Criterio de ordenamiento.
- **Response Exitosa (`200 OK`):**
  ```json
  {
      "success": true,
      "message": "Listado de aplicativos obtenido exitosamente.",
      "data": {
          "total": 1,
          "aplicativos": [
              {
                  "id": 1,
                  "nombre": "ERP SAP",
                  "url": "https://sap.empresa.com",
                  "logo": "https://sap.empresa.com/logo.svg",
                  "logo_url": "https://sap.empresa.com/logo.svg",
                  "logo_archivo": null,
                  "descripcion": "Planificación de recursos empresariales",
                  "orden": 1,
                  "activo": true,
                  "grupos_ad": ["Ventas_Chile", "GPO_ERP_Users"],
                  "departamentos_ad": ["Comercial", "Ventas"],
                  "permiso_requerido": "aplicativos.acceso_sap",
                  "grupos": ["Finanzas_Staff"],
                  "permisos": ["aplicativos.acceso_sap"],
                  "created_at": "2026-10-06T22:00:00Z",
                  "updated_at": "2026-10-06T22:00:00Z"
              }
          ]
      }
  }
  ```

#### B. Crear Nuevo Aplicativo
- **Ruta:** `/{API_PREFIX}aplicativos/` (por defecto: `/api/v1/aplicativos/`)
- **Método:** `POST`
- **Content-Type:** `application/json` o `multipart/form-data`
- **Campos requeridos:** `nombre`, `url`
- **Campos opcionales:**
  - `grupos_ad` (cadena o lista de grupos de Active Directory, ej: `["Ventas_Chile", "GPO_ERP"]`)
  - `departamentos_ad` (cadena o lista de departamentos de AD, ej: `["Comercial", "Finanzas"]`)
  - `logo` (URL o ícono web)
  - `logo_archivo` (archivo PNG, SVG, JPG, WebP)
  - `descripcion` (texto explicativo)
  - `orden` (número entero de prioridad)
  - `activo` (booleano)
  - `permiso_requerido` (cadena de texto con permiso Django o grupo AD)
  - `grupos` (lista de nombres o IDs de grupos Django)
  - `permisos` (lista de codenames o IDs de permisos Django)
- **Response Exitosa (`201 Created`):**
  ```json
  {
      "success": true,
      "message": "Aplicativo 'ERP SAP' creado exitosamente.",
      "data": { ... }
  }
  ```

#### C. Detalle de un Aplicativo
- **Ruta:** `/{API_PREFIX}aplicativos/<id>/`
- **Método:** `GET`
- **Validación de Seguridad:**
  - Si el usuario cuenta con el permiso o es superusuario: `200 OK`.
  - Si el usuario está autenticado pero no tiene los permisos: `403 Forbidden` (`PERMISSION_DENIED`).
  - Si el aplicativo requiere permisos y el usuario es anónimo: `401 Unauthorized` (`UNAUTHORIZED`).

#### D. Actualizar Aplicativo
- **Ruta:** `/{API_PREFIX}aplicativos/<id>/`
- **Método:** `PUT` / `PATCH`
- **Campos modificables:** `nombre`, `url`, `logo`, `logo_archivo`, `descripcion`, `orden`, `activo`, `permiso_requerido`, `grupos`, `permisos`.

#### E. Eliminar Aplicativo
- **Ruta:** `/{API_PREFIX}aplicativos/<id>/`
- **Método:** `DELETE`
- **Response Exitosa (`200 OK`):**
  ```json
  {
      "success": true,
      "message": "Aplicativo 'ERP SAP' eliminado exitosamente.",
      "data": { "id": 1, "nombre": "ERP SAP" }
  }
  ```

---

## 5. Próxima Etapa de Implementación

La creación de vistas por función se organizará modularmente:
1. [backend/Dashboard/urls.py](file:///d:/PerfilUsuario/Desktop/GestionComercial/backend/Dashboard/urls.py): Enrutamiento modular de los endpoints de la API.
2. `backend/Dashboard/views_auth.py`: Funciones para `api_login`, `api_logout`, `api_me`.
3. `backend/Dashboard/views_profile.py`: Funciones para consultar y actualizar perfil.
4. `backend/Dashboard/views_dashboard.py`: Funciones con métricas y resumen comercial.
5. Inclusión automática en [backend/core/urls.py](file:///d:/PerfilUsuario/Desktop/GestionComercial/backend/core/urls.py) bajo `path(settings.API_PREFIX, include('Dashboard.urls'))`.
