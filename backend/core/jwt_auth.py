import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse


class JwtAuthError(Exception):
    def __init__(self, message, code="INVALID_TOKEN", status=401):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class JwtExpiredError(JwtAuthError):
    def __init__(self, message="El token de acceso ha expirado."):
        super().__init__(message, code="TOKEN_EXPIRED", status=401)


class JwtInvalidError(JwtAuthError):
    def __init__(self, message="El token suministrado no es válido o la firma es incorrecta."):
        super().__init__(message, code="INVALID_TOKEN", status=401)


def generate_jwt_tokens(user):
    """
    Genera un par de tokens JWT (access_token y refresh_token) criptográficamente firmados
    con expiración temporal estricta para el usuario.
    """
    now = datetime.now(timezone.utc)
    access_minutes = getattr(settings, 'JWT_ACCESS_EXPIRATION_MINUTES', 60)
    refresh_days = getattr(settings, 'JWT_REFRESH_EXPIRATION_DAYS', 7)
    secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
    algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')

    access_exp = now + timedelta(minutes=access_minutes)
    refresh_exp = now + timedelta(days=refresh_days)

    access_payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email or '',
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'token_type': 'access',
        'iat': int(now.timestamp()),
        'exp': int(access_exp.timestamp()),
    }

    refresh_payload = {
        'user_id': user.id,
        'username': user.username,
        'token_type': 'refresh',
        'iat': int(now.timestamp()),
        'exp': int(refresh_exp.timestamp()),
    }

    access_token = jwt.encode(access_payload, secret_key, algorithm=algorithm)
    refresh_token = jwt.encode(refresh_payload, secret_key, algorithm=algorithm)

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': access_minutes * 60,
        'expires_at': access_exp.isoformat(),
    }


def decode_jwt_token(token, expected_type='access'):
    """
    Valida la firma, integridad y fecha de expiración del token JWT.
    Retorna el payload decodificado si es válido, o lanza JwtAuthError.
    """
    secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
    algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options={'require': ['exp', 'iat', 'user_id', 'token_type']}
        )
    except jwt.ExpiredSignatureError:
        raise JwtExpiredError()
    except jwt.InvalidTokenError as e:
        raise JwtInvalidError(f"Token inválido: {str(e)}")

    token_type = payload.get('token_type')
    if token_type != expected_type:
        raise JwtInvalidError(f"Tipo de token incorrecto. Se esperaba '{expected_type}', se recibió '{token_type}'.")

    return payload


def get_user_from_request(request):
    """
    Extrae e identifica de forma segura el usuario autenticado desde el encabezado
    HTTP Authorization (Bearer <token>) o desde la sesión activa de Django.
    Retorna (user, error_dict).
    """
    auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION', '')

    if auth_header:
        parts = auth_header.strip().split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None, {
                'error': "Encabezado Authorization malformado. Formato esperado: 'Bearer <token>'.",
                'code': "MALFORMED_AUTHORIZATION_HEADER",
                'status': 401
            }

        token = parts[1]
        try:
            payload = decode_jwt_token(token, expected_type='access')
        except JwtAuthError as err:
            return None, {
                'error': err.message,
                'code': err.code,
                'status': err.status
            }

        user_id = payload.get('user_id')
        user = User.objects.filter(id=user_id, is_active=True).first()
        if not user:
            return None, {
                'error': "El usuario asociado a este token no existe o ha sido desactivado.",
                'code': "USER_NOT_FOUND_OR_INACTIVE",
                'status': 401
            }

        return user, None

    # Fallback seguro: Si no viene Authorization header, verificar sesión local autenticada
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user, None

    return None, {
        'error': "Autenticación requerida. Debe proporcionar un token JWT en el encabezado 'Authorization: Bearer <token>'.",
        'code': "UNAUTHORIZED",
        'status': 401
    }


def jwt_required(view_func):
    """
    Decorador estricto para endpoints de la API REST.
    Exige un token JWT válido (o sesión autenticada) con expiración vigente.
    Rechaza solicitudes anónimas con HTTP 401 Unauthorized y código explicativo.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user, error = get_user_from_request(request)
        if error:
            return JsonResponse({
                'success': False,
                'error': error['error'],
                'code': error['code']
            }, status=error['status'])

        # Inyecta el usuario validado en el objeto request
        request.user = user
        return view_func(request, *args, **kwargs)

    return _wrapped_view
