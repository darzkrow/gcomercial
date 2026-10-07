import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth.models import Group, Permission
from Dashboard.utils import json_success, json_error, parse_json_body
from core.jwt_auth import jwt_required
from .models import Aplicativo


url_validator = URLValidator()


def _extract_request_data(request):
    """
    Extrae los datos de la solicitud ya sea que vengan como JSON en el body
    o como multipart/form-data (por ejemplo si se sube un archivo).
    """
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.POST.dict()
        return data, None
    return parse_json_body(request)


def _normalize_ad_list(value):
    """Normaliza un valor de grupos o departamentos de AD (lista o string separado por coma)."""
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    elif isinstance(value, str):
        return value.strip()
    return ""


def _sync_grupos_and_permisos(aplicativo, data):
    """Sincroniza relaciones ManyToMany de grupos y permisos si vienen en el payload."""
    if 'grupos' in data:
        grupos_data = data['grupos']
        if isinstance(grupos_data, list):
            grupos_objs = []
            for g in grupos_data:
                if isinstance(g, int) or (isinstance(g, str) and g.isdigit()):
                    grupo = Group.objects.filter(id=int(g)).first()
                else:
                    grupo = Group.objects.filter(name__iexact=str(g).strip()).first()
                if grupo:
                    grupos_objs.append(grupo)
            aplicativo.grupos.set(grupos_objs)

    if 'permisos' in data:
        permisos_data = data['permisos']
        if isinstance(permisos_data, list):
            perm_objs = []
            for p in permisos_data:
                if isinstance(p, int) or (isinstance(p, str) and p.isdigit()):
                    perm = Permission.objects.filter(id=int(p)).first()
                else:
                    p_str = str(p).strip()
                    if '.' in p_str:
                        app_lbl, cname = p_str.split('.', 1)
                        perm = Permission.objects.filter(content_type__app_label=app_lbl, codename=cname).first()
                    else:
                        perm = Permission.objects.filter(codename=p_str).first()
                if perm:
                    perm_objs.append(perm)
            aplicativo.permisos.set(perm_objs)


@csrf_exempt
@jwt_required
@require_http_methods(["GET", "POST"])
def api_aplicativos_list_create(request):
    """
    GET /{API_PREFIX}aplicativos/
        Retorna la lista de aplicativos a los que el usuario solicitante tiene acceso
        según sus grupos de Active Directory (AD / LDAP), departamento corporativo o permisos.

    POST /{API_PREFIX}aplicativos/
        Crea un nuevo aplicativo.
        Soporta configuración nativa de Active Directory:
        - grupos_ad (str | list[str], ej: ["Ventas_Chile", "GPO_ERP"])
        - departamentos_ad (str | list[str], ej: ["Comercial", "Finanzas"])
        - permiso_requerido (str)
        - grupos (list[str|int])
        - permisos (list[str|int])
    """
    if request.method == "GET":
        qs = Aplicativo.objects.all().prefetch_related('grupos', 'permisos')

        # Filtro por estado activo/inactivo
        activo_param = request.GET.get('activo')
        if activo_param is not None:
            if activo_param.lower() in ['true', '1', 'yes']:
                qs = qs.filter(activo=True)
            elif activo_param.lower() in ['false', '0', 'no']:
                qs = qs.filter(activo=False)

        # Filtro de búsqueda textual
        search_query = request.GET.get('search', '').strip()
        if search_query:
            qs = qs.filter(
                Q(nombre__icontains=search_query) |
                Q(descripcion__icontains=search_query) |
                Q(url__icontains=search_query) |
                Q(grupos_ad__icontains=search_query) |
                Q(departamentos_ad__icontains=search_query)
            )

        # Ordenamiento
        order_param = request.GET.get('order_by', 'orden')
        allowed_order_fields = ['orden', '-orden', 'nombre', '-nombre', 'created_at', '-created_at']
        if order_param in allowed_order_fields:
            qs = qs.order_by(order_param)
        else:
            qs = qs.order_by('orden', 'nombre')

        # Filtro de seguridad: Sólo incluir aplicativos a los que el usuario tiene acceso
        items = [app.to_dict(request=request) for app in qs if app.tiene_acceso(request.user)]

        return json_success(
            data={
                "total": len(items),
                "aplicativos": items,
            },
            message="Listado de aplicativos obtenido exitosamente."
        )

    elif request.method == "POST":
        data, parse_err = _extract_request_data(request)
        if parse_err:
            return parse_err

        nombre = str(data.get('nombre', '')).strip()
        url = str(data.get('url', '')).strip()
        logo = str(data.get('logo', '')).strip()
        descripcion = str(data.get('descripcion', '')).strip()
        orden = data.get('orden', 0)
        activo = data.get('activo', True)
        permiso_requerido = str(data.get('permiso_requerido', '')).strip()
        grupos_ad = _normalize_ad_list(data.get('grupos_ad', ''))
        departamentos_ad = _normalize_ad_list(data.get('departamentos_ad', ''))

        # Validaciones de campos obligatorios
        if not nombre:
            return json_error("El campo 'nombre' es obligatorio.", status=400, code="MISSING_NAME")

        if not url:
            return json_error("El campo 'url' es obligatorio.", status=400, code="MISSING_URL")

        # Validación de formato de URL
        try:
            url_validator(url)
        except ValidationError:
            return json_error("El formato de la 'url' no es válido. Debe incluir el protocolo (ej. https://...).", status=400, code="INVALID_URL")

        # Validación de unicidad de nombre
        if Aplicativo.objects.filter(nombre__iexact=nombre).exists():
            return json_error(f"Ya existe un aplicativo registrado con el nombre '{nombre}'.", status=400, code="DUPLICATE_NAME")

        # Validación de orden numérico
        try:
            orden = int(orden)
        except (ValueError, TypeError):
            orden = 0

        # Normalización de valor booleano activo
        if isinstance(activo, str):
            activo = activo.lower() in ['true', '1', 'yes']
        else:
            activo = bool(activo)

        # Manejo de archivo de logo si se envía por multipart
        logo_archivo = request.FILES.get('logo_archivo')

        aplicativo = Aplicativo.objects.create(
            nombre=nombre,
            url=url,
            logo=logo,
            logo_archivo=logo_archivo,
            descripcion=descripcion,
            orden=orden,
            activo=activo,
            grupos_ad=grupos_ad,
            departamentos_ad=departamentos_ad,
            permiso_requerido=permiso_requerido,
        )

        # Sincronizar grupos y permisos si fueron provistos
        _sync_grupos_and_permisos(aplicativo, data)

        return json_success(
            data=aplicativo.to_dict(request=request),
            message=f"Aplicativo '{aplicativo.nombre}' creado exitosamente.",
            status=201
        )


@csrf_exempt
@jwt_required
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def api_aplicativo_detail(request, pk):
    """
    GET /{API_PREFIX}aplicativos/<pk>/
        Obtiene los detalles del aplicativo por ID.
        Verifica que el usuario tenga los permisos necesarios para ver este aplicativo.

    PUT / PATCH /{API_PREFIX}aplicativos/<pk>/
        Actualiza los campos de un aplicativo existente, incluyendo sus grupos y departamentos de AD.

    DELETE /{API_PREFIX}aplicativos/<pk>/
        Elimina el aplicativo especificado.
    """
    try:
        aplicativo = Aplicativo.objects.prefetch_related('grupos', 'permisos').get(pk=pk)
    except Aplicativo.DoesNotExist:
        return json_error(f"No se encontró ningún aplicativo con ID {pk}.", status=404, code="NOT_FOUND")

    if request.method == "GET":
        # Verificación estricta de permisos de visualización
        if not aplicativo.tiene_acceso(request.user):
            if not request.user or not request.user.is_authenticated:
                return json_error(
                    "Autenticación requerida para acceder a este aplicativo.",
                    status=401,
                    code="UNAUTHORIZED"
                )
            return json_error(
                f"No cuenta con los permisos necesarios para visualizar el aplicativo '{aplicativo.nombre}'.",
                status=403,
                code="PERMISSION_DENIED"
            )

        return json_success(
            data=aplicativo.to_dict(request=request),
            message="Detalle de aplicativo obtenido exitosamente."
        )

    elif request.method in ["PUT", "PATCH"]:
        data, parse_err = _extract_request_data(request)
        if parse_err:
            return parse_err

        # Si se envía nombre, validar unicidad
        if 'nombre' in data:
            nombre = str(data['nombre']).strip()
            if not nombre:
                return json_error("El campo 'nombre' no puede estar vacío.", status=400, code="EMPTY_NAME")
            if Aplicativo.objects.filter(nombre__iexact=nombre).exclude(pk=aplicativo.pk).exists():
                return json_error(f"Ya existe otro aplicativo registrado con el nombre '{nombre}'.", status=400, code="DUPLICATE_NAME")
            aplicativo.nombre = nombre

        # Si se envía url, validar sintaxis
        if 'url' in data:
            url = str(data['url']).strip()
            if not url:
                return json_error("El campo 'url' no puede estar vacío.", status=400, code="EMPTY_URL")
            try:
                url_validator(url)
            except ValidationError:
                return json_error("El formato de la 'url' no es válido. Debe incluir el protocolo (ej. https://...).", status=400, code="INVALID_URL")
            aplicativo.url = url

        if 'logo' in data:
            aplicativo.logo = str(data['logo']).strip()

        if 'descripcion' in data:
            aplicativo.descripcion = str(data['descripcion']).strip()

        if 'orden' in data:
            try:
                aplicativo.orden = int(data['orden'])
            except (ValueError, TypeError):
                pass

        if 'activo' in data:
            val = data['activo']
            if isinstance(val, str):
                aplicativo.activo = val.lower() in ['true', '1', 'yes']
            else:
                aplicativo.activo = bool(val)

        if 'grupos_ad' in data:
            aplicativo.grupos_ad = _normalize_ad_list(data['grupos_ad'])

        if 'departamentos_ad' in data:
            aplicativo.departamentos_ad = _normalize_ad_list(data['departamentos_ad'])

        if 'permiso_requerido' in data:
            aplicativo.permiso_requerido = str(data['permiso_requerido']).strip()

        # Manejo de reemplazo de archivo si fue provisto
        if 'logo_archivo' in request.FILES:
            aplicativo.logo_archivo = request.FILES['logo_archivo']

        aplicativo.save()

        # Sincronizar grupos y permisos si vienen en el payload
        _sync_grupos_and_permisos(aplicativo, data)

        return json_success(
            data=aplicativo.to_dict(request=request),
            message=f"Aplicativo '{aplicativo.nombre}' actualizado exitosamente."
        )

    elif request.method == "DELETE":
        nombre_eliminado = aplicativo.nombre
        aplicativo_id = aplicativo.id
        aplicativo.delete()
        return json_success(
            data={"id": aplicativo_id, "nombre": nombre_eliminado},
            message=f"Aplicativo '{nombre_eliminado}' eliminado exitosamente."
        )
