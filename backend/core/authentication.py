import logging
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from Dashboard.models import UserProfile
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException

logger = logging.getLogger(__name__)


class ActiveDirectoryBackend(ModelBackend):
    """
    Backend de autenticación contra Active Directory (AD / LDAP).
    Permite:
    1. Autenticar credenciales contra el servidor de dominio.
    2. Validar pertenencia a grupos de seguridad / GPO para permitir el acceso.
    3. Crear y sincronizar automáticamente el User de Django y su UserProfile
       (nombre, apellido, email, cargo, departamento, teléfono y grupos).
    4. Mapear grupos de AD a permisos de Staff y Superusuario en Django.
    """

    def _extract_cn(self, dn_str):
        """Extrae el CN (Common Name) de un Distinguished Name."""
        if not dn_str:
            return ""
        for part in str(dn_str).split(','):
            part = part.strip()
            if part.upper().startswith('CN='):
                return part[3:].strip()
        return str(dn_str).strip()

    def authenticate(self, request, username=None, password=None, **kwargs):
        # 1. Si LDAP está deshabilitado en configuración, delegar al siguiente backend
        if not getattr(settings, 'LDAP_ENABLED', False):
            return None

        if not username or not password:
            return None

        # 2. Normalizar el nombre de usuario y dominio
        username = str(username).strip()
        clean_username = username
        domain = getattr(settings, 'LDAP_DOMAIN', '')

        # Si viene en formato DOMINIO\usuario
        if '\\' in clean_username:
            domain, clean_username = clean_username.split('\\', 1)
        # Si viene en formato usuario@dominio.com
        elif '@' in clean_username:
            clean_username, domain_part = clean_username.split('@', 1)
            if not domain:
                domain = domain_part

        clean_username = clean_username.strip()

        # 3. Configurar servidor LDAP
        server_uri = getattr(settings, 'LDAP_SERVER_URI', 'ldap://127.0.0.1:389')
        port = getattr(settings, 'LDAP_PORT', 389)
        use_ssl = getattr(settings, 'LDAP_USE_SSL', False)
        timeout = getattr(settings, 'LDAP_CONNECT_TIMEOUT', 5)

        try:
            server = Server(server_uri, port=port, use_ssl=use_ssl, connect_timeout=timeout, get_info=ALL)
        except Exception as e:
            logger.error(f"AD/LDAP: Error al inicializar servidor {server_uri}: {e}")
            return None

        search_base = getattr(settings, 'LDAP_SEARCH_BASE', '')
        bind_dn = getattr(settings, 'LDAP_BIND_DN', '')
        bind_password = getattr(settings, 'LDAP_BIND_PASSWORD', '')

        attributes_to_fetch = [
            'distinguishedName',
            'sAMAccountName',
            'userPrincipalName',
            'givenName',
            'sn',
            'mail',
            'department',
            'title',
            'telephoneNumber',
            'memberOf',
        ]

        entry = None
        user_dn = None

        try:
            # 4. Modo de conexión:
            # CASO A: Con cuenta de servicio (Recomendado para Active Directory corporativo)
            if bind_dn and bind_password:
                service_conn = Connection(
                    server,
                    user=bind_dn,
                    password=bind_password,
                    auto_bind=True,
                    receive_timeout=timeout
                )

                # Buscar al usuario por sAMAccountName o userPrincipalName
                upn = f"{clean_username}@{domain}" if domain else clean_username
                search_filter = (
                    f"(&(objectCategory=person)(objectClass=user)"
                    f"(|(sAMAccountName={clean_username})(userPrincipalName={upn})))"
                )

                service_conn.search(
                    search_base=search_base,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=attributes_to_fetch
                )

                if not service_conn.entries:
                    logger.warning(f"AD/LDAP: Usuario '{clean_username}' no encontrado en el directorio.")
                    service_conn.unbind()
                    return None

                entry = service_conn.entries[0]
                user_dn = str(entry.entry_dn)
                service_conn.unbind()

                # Validar la contraseña del usuario haciendo bind con su DN
                user_conn = Connection(server, user=user_dn, password=password, receive_timeout=timeout)
                if not user_conn.bind():
                    logger.warning(f"AD/LDAP: Contraseña inválida para el usuario '{clean_username}'.")
                    return None
                user_conn.unbind()

            # CASO B: Bind directo del usuario (cuando no hay cuenta de servicio)
            else:
                user_bind = f"{domain}\\{clean_username}" if domain else clean_username
                user_conn = Connection(server, user=user_bind, password=password, receive_timeout=timeout)
                if not user_conn.bind():
                    logger.warning(f"AD/LDAP: Credenciales inválidas para '{clean_username}'.")
                    return None

                # Si el bind fue exitoso, consultar sus atributos si search_base está disponible
                if search_base:
                    search_filter = f"(&(objectCategory=person)(objectClass=user)(sAMAccountName={clean_username}))"
                    user_conn.search(
                        search_base=search_base,
                        search_filter=search_filter,
                        search_scope=SUBTREE,
                        attributes=attributes_to_fetch
                    )
                    if user_conn.entries:
                        entry = user_conn.entries[0]
                        user_dn = str(entry.entry_dn)

                user_conn.unbind()

        except LDAPException as e:
            logger.error(f"AD/LDAP: Excepción de comunicación con Active Directory: {e}")
            return None
        except Exception as e:
            logger.error(f"AD/LDAP: Error inesperado durante autenticación de '{clean_username}': {e}")
            return None

        # 5. Obtener grupos a los que pertenece el usuario
        raw_groups = []
        if entry and hasattr(entry, 'memberOf') and entry.memberOf:
            raw_groups = list(entry.memberOf.values)

        group_cns = [self._extract_cn(g) for g in raw_groups]

        # 6. Validación de Grupo Requerido / GPO
        required_groups = [g.strip() for g in getattr(settings, 'LDAP_REQUIRED_GROUPS', []) if g.strip()]
        if required_groups:
            # Comprueba si el usuario pertenece al menos a uno de los grupos autorizados
            has_access = any(
                req.lower() in [g.lower() for g in group_cns] or
                req.lower() in [g.lower() for g in raw_groups]
                for req in required_groups
            )

            if not has_access:
                logger.warning(
                    f"AD/LDAP: Acceso DENEGADO. El usuario '{clean_username}' se autenticó pero "
                    f"no pertenece a los grupos autorizados: {required_groups}. Grupos del usuario: {group_cns}"
                )
                return None

        # 7. Mapeo de permisos de Django según grupos de AD
        staff_groups = [g.strip() for g in getattr(settings, 'LDAP_STAFF_GROUPS', []) if g.strip()]
        superuser_groups = [g.strip() for g in getattr(settings, 'LDAP_SUPERUSER_GROUPS', []) if g.strip()]

        is_superuser = any(
            sg.lower() in [g.lower() for g in group_cns] or sg.lower() in [g.lower() for g in raw_groups]
            for sg in superuser_groups
        )
        is_staff = is_superuser or any(
            sg.lower() in [g.lower() for g in group_cns] or sg.lower() in [g.lower() for g in raw_groups]
            for sg in staff_groups
        )

        # 8. Creación o actualización del Usuario Django y su Perfil
        user, created = User.objects.get_or_create(username=clean_username)

        # Extraer atributos básicos de AD
        if entry:
            first_name = str(getattr(entry, 'givenName', '') or '').strip()
            last_name = str(getattr(entry, 'sn', '') or '').strip()
            mail = str(getattr(entry, 'mail', '') or getattr(entry, 'userPrincipalName', '') or '').strip()

            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if mail:
                user.email = mail

        # Solo modificar flags de permisos si hay grupos de staff/superuser configurados
        if staff_groups or superuser_groups:
            user.is_staff = is_staff
            user.is_superuser = is_superuser

        user.is_active = True
        user.save()

        # 9. Crear o actualizar el UserProfile con los datos de Active Directory
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if entry:
            if hasattr(entry, 'department') and entry.department.value:
                profile.department = str(entry.department.value)
            if hasattr(entry, 'title') and entry.title.value:
                profile.job_title = str(entry.title.value)
            if hasattr(entry, 'telephoneNumber') and entry.telephoneNumber.value:
                profile.phone = str(entry.telephoneNumber.value)

        if user_dn:
            profile.ad_dn = user_dn
        if group_cns:
            profile.ad_groups = ", ".join(group_cns)

        profile.save()

        action = "creado" if created else "sincronizado"
        logger.info(f"AD/LDAP: Usuario '{clean_username}' autenticado exitosamente y perfil {action}.")
        return user
