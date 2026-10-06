import json
from functools import wraps
from django.http import JsonResponse


def json_success(data=None, message="Operación exitosa", status=200):
    """Genera una respuesta JSON exitosa con estructura estándar."""
    response_payload = {
        "success": True,
        "message": message,
    }
    if data is not None:
        response_payload["data"] = data
    return JsonResponse(response_payload, status=status)


def json_error(error, status=400, code="ERROR", details=None):
    """Genera una respuesta JSON de error con estructura estándar."""
    response_payload = {
        "success": False,
        "error": error,
        "code": code,
    }
    if details is not None:
        response_payload["details"] = details
    return JsonResponse(response_payload, status=status)


def parse_json_body(request):
    """
    Parsea de forma segura el cuerpo de una petición JSON.
    Retorna una tupla (data_dict, error_response).
    Si hay error de parseo, data_dict es None y error_response contiene el JsonResponse 400.
    """
    if not request.body:
        return {}, None
    try:
        data = json.loads(request.body.decode('utf-8'))
        if not isinstance(data, dict):
            return None, json_error("El cuerpo de la solicitud debe ser un objeto JSON.", status=400, code="INVALID_FORMAT")
        return data, None
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return None, json_error("El cuerpo de la solicitud no es un JSON válido.", status=400, code="INVALID_JSON", details=str(e))


def serialize_user(user):
    """Serializa un User de Django y su UserProfile extendido a diccionario."""
    profile_data = {}
    if hasattr(user, 'profile'):
        p = user.profile
        profile_data = {
            "department": p.department or "",
            "job_title": p.job_title or "",
            "phone": p.phone or "",
            "ad_dn": p.ad_dn or "",
            "ad_groups": [g.strip() for g in p.ad_groups.split(',') if g.strip()] if p.ad_groups else [],
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }

    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.get_full_name() or user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        "profile": profile_data,
    }


def api_login_required(view_func):
    """
    Decorador para endpoints API REST que exige autenticación.
    Si el usuario no está autenticado, devuelve 401 Unauthorized en JSON.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return json_error(
                "Autenticación requerida. Por favor inicie sesión.",
                status=401,
                code="UNAUTHORIZED"
            )
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def api_staff_required(view_func):
    """
    Decorador para endpoints API REST que exige privilegios de Staff.
    Devuelve 403 Forbidden en JSON si no cuenta con permisos.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return json_error("Autenticación requerida.", status=401, code="UNAUTHORIZED")
        if not request.user.is_staff:
            return json_error(
                "Acceso restringido. Se requieren permisos de administración (Staff).",
                status=403,
                code="FORBIDDEN"
            )
        return view_func(request, *args, **kwargs)
    return _wrapped_view
