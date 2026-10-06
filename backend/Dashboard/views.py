from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.conf import settings
from .models import UserProfile
from .utils import (
    json_success,
    json_error,
    parse_json_body,
    serialize_user,
    api_login_required,
    api_staff_required,
)


# ==============================================================================
# 1. AUTENTICACIÓN Y SESIÓN
# ==============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """
    POST /{API_PREFIX}auth/login/
    Inicia sesión validando credenciales contra Active Directory (AD/LDAP) o base local.
    Verifica pertenencia a grupos/GPO autorizados y sincroniza el perfil.
    """
    data, error = parse_json_body(request)
    if error:
        return error

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()
    remember_me = bool(data.get("remember_me", False))

    if not username or not password:
        return json_error(
            "Los campos 'username' y 'password' son obligatorios.",
            status=400,
            code="MISSING_CREDENTIALS"
        )

    # Intento de autenticación (AD primero, luego fallback a ModelBackend)
    user = authenticate(request, username=username, password=password)

    if user is None:
        return json_error(
            "Credenciales inválidas o acceso no autorizado por política de grupo.",
            status=401,
            code="INVALID_CREDENTIALS"
        )

    if not user.is_active:
        return json_error(
            "La cuenta de usuario se encuentra deshabilitada o inactiva.",
            status=403,
            code="USER_INACTIVE"
        )

    # Iniciar sesión en el request
    login(request, user)

    # Configurar expiración de sesión
    if remember_me:
        request.session.set_expiry(1209600)  # 2 semanas
    else:
        request.session.set_expiry(0)  # Expira al cerrar el navegador

    return json_success(
        data={"user": serialize_user(user)},
        message=f"Bienvenido/a, {user.get_full_name() or user.username}."
    )


@csrf_exempt
@require_http_methods(["POST"])
@api_login_required
def api_logout(request):
    """
    POST /{API_PREFIX}auth/logout/
    Cierra la sesión activa del usuario.
    """
    username = request.user.username
    logout(request)
    return json_success(message=f"Sesión cerrada correctamente para el usuario '{username}'.")


@require_http_methods(["GET"])
@api_login_required
def api_me(request):
    """
    GET /{API_PREFIX}auth/me/
    Retorna los datos del usuario autenticado en la sesión actual.
    """
    return json_success(data={"user": serialize_user(request.user)})


# ==============================================================================
# 2. GESTIÓN DE PERFILES
# ==============================================================================

@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH"])
@api_login_required
def api_profile(request):
    """
    GET, PUT, PATCH /{API_PREFIX}profile/
    Consulta o actualiza la información del perfil del usuario conectado.
    """
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == "GET":
        return json_success(data=serialize_user(user))

    # Métodos PUT / PATCH: actualización de datos de contacto
    data, error = parse_json_body(request)
    if error:
        return error

    user_modified = False
    profile_modified = False

    # Campos de User
    if "first_name" in data:
        user.first_name = str(data["first_name"]).strip()
        user_modified = True
    if "last_name" in data:
        user.last_name = str(data["last_name"]).strip()
        user_modified = True
    if "email" in data:
        user.email = str(data["email"]).strip()
        user_modified = True

    # Campos de UserProfile
    if "phone" in data:
        profile.phone = str(data["phone"]).strip()
        profile_modified = True
    if "job_title" in data:
        profile.job_title = str(data["job_title"]).strip()
        profile_modified = True
    if "department" in data:
        profile.department = str(data["department"]).strip()
        profile_modified = True

    if user_modified:
        user.save()
    if profile_modified:
        profile.save()

    return json_success(
        data=serialize_user(user),
        message="Perfil actualizado correctamente."
    )


# ==============================================================================
# 3. MÉTRICAS Y DASHBOARD
# ==============================================================================

@require_http_methods(["GET"])
@api_login_required
def api_dashboard_stats(request):
    """
    GET /{API_PREFIX}dashboard/stats/
    Retorna métricas globales del sistema, resumen de usuarios y departamentos.
    """
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superuser_users = User.objects.filter(is_superuser=True).count()

    # Distribución por departamentos
    departments_qs = (
        UserProfile.objects.exclude(department__isnull=True)
        .exclude(department="")
        .values("department")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    departments = [{"name": item["department"], "count": item["total"]} for item in departments_qs]

    stats = {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
            "staff": staff_users,
            "superusers": superuser_users,
        },
        "departments": departments,
        "system": {
            "environment": "production" if getattr(settings, 'PRODUCTION', False) else "development",
            "database_engine": settings.DATABASES["default"]["ENGINE"].split(".")[-1],
            "ldap_enabled": getattr(settings, 'LDAP_ENABLED', False),
            "api_version": settings.API_PREFIX.strip("/"),
        },
    }

    return json_success(data=stats, message="Estadísticas obtenidas correctamente.")


@require_http_methods(["GET"])
@api_staff_required
def api_users_list(request):
    """
    GET /{API_PREFIX}users/
    Lista usuarios con soporte para búsqueda y paginación. Requiere permisos de Staff.
    Parámetros de consulta opcionales:
      - ?q=termino_de_busqueda
      - ?page=1
      - ?limit=20
    """
    query = request.GET.get("q", "").strip()
    try:
        page = max(1, int(request.GET.get("page", 1)))
        limit = min(100, max(1, int(request.GET.get("limit", 20))))
    except ValueError:
        return json_error("Los parámetros 'page' y 'limit' deben ser números enteros válidos.", status=400)

    users_qs = User.objects.select_related("profile").order_by("username")

    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(profile__department__icontains=query)
            | Q(profile__job_title__icontains=query)
        )

    total_records = users_qs.count()
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paged_users = users_qs[start_idx:end_idx]

    serialized = [serialize_user(u) for u in paged_users]

    total_pages = (total_records + limit - 1) // limit if total_records > 0 else 1

    return json_success(
        data={
            "users": serialized,
            "pagination": {
                "total": total_records,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }
    )


# ==============================================================================
# 4. SALUD DEL SERVICIO
# ==============================================================================

@require_http_methods(["GET"])
def api_health(request):
    """
    GET /{API_PREFIX}health/
    Health check público para monitoreo del backend.
    """
    return json_success(
        data={
            "status": "healthy",
            "service": "GestionComercial Backend API",
            "api_version": settings.API_PREFIX.strip("/"),
        },
        message="Servicio operativo."
    )
