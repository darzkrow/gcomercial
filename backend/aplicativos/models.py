from django.db import models
from django.contrib.auth.models import Group, Permission


class Aplicativo(models.Model):
    """
    Modelo para almacenar los enlaces, logos y nombres de diferentes aplicativos externos
    o internos vinculados a la plataforma de Gestión Comercial.
    Soporta control de acceso y visibilidad nativo contra Active Directory (AD / LDAP)
    así como permisos y grupos de Django.
    """
    nombre = models.CharField(
        'Nombre del Aplicativo',
        max_length=150,
        unique=True,
        help_text='Nombre identificador del aplicativo o sistema externo'
    )
    url = models.URLField(
        'URL del Aplicativo',
        max_length=500,
        help_text='Enlace o dirección web de acceso al aplicativo'
    )
    logo = models.CharField(
        'Logo / Ícono',
        max_length=500,
        blank=True,
        default='',
        help_text='URL de imagen web o clase de ícono SVG/FontAwesome'
    )
    logo_archivo = models.FileField(
        'Archivo de Logo',
        upload_to='aplicativos/logos/',
        blank=True,
        null=True,
        help_text='Archivo opcional subido localmente (PNG, SVG, JPG, WebP)'
    )
    descripcion = models.CharField(
        'Descripción',
        max_length=255,
        blank=True,
        default='',
        help_text='Breve descripción de la funcionalidad del aplicativo'
    )
    orden = models.PositiveIntegerField(
        'Orden de Visualización',
        default=0,
        help_text='Prioridad para el ordenamiento en la interfaz (menor número = primero)'
    )
    activo = models.BooleanField(
        'Activo',
        default=True,
        help_text='Indica si el enlace está habilitado y visible en el portal'
    )

    # --------------------------------------------------------------------------
    # Control de Acceso Nativo Active Directory (AD / LDAP)
    # --------------------------------------------------------------------------
    grupos_ad = models.TextField(
        'Grupos de Active Directory (AD / LDAP)',
        blank=True,
        default='',
        help_text='Grupos de seguridad o distribución de AD autorizados (separados por coma, ej: Ventas_Chile, Finanzas_Staff, GPO_ERP_Users)'
    )
    departamentos_ad = models.CharField(
        'Departamentos de Active Directory',
        max_length=255,
        blank=True,
        default='',
        help_text='Departamentos corporativos de Active Directory autorizados (separados por coma, ej: Comercial, Finanzas, TI)'
    )

    # --------------------------------------------------------------------------
    # Control de Acceso y Permisos de Django
    # --------------------------------------------------------------------------
    permiso_requerido = models.CharField(
        'Permiso Requerido',
        max_length=150,
        blank=True,
        default='',
        help_text='Permiso Django (ej. "aplicativos.view_crm"), código de permiso o grupo requerido'
    )
    grupos = models.ManyToManyField(
        Group,
        blank=True,
        related_name='aplicativos',
        verbose_name='Grupos con Acceso',
        help_text='Grupos de Django autorizados para visualizar este aplicativo'
    )
    permisos = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='aplicativos',
        verbose_name='Permisos Django Requeridos',
        help_text='Permisos específicos de Django requeridos para visualizar este aplicativo'
    )

    created_at = models.DateTimeField(
        'Fecha de Creación',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Última Actualización',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Aplicativo'
        verbose_name_plural = 'Aplicativos'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

    def get_grupos_ad_list(self):
        """Retorna la lista de grupos de AD requeridos en minúsculas y sin espacios."""
        if not self.grupos_ad:
            return []
        return [g.strip().lower() for g in self.grupos_ad.split(',') if g.strip()]

    def get_departamentos_ad_list(self):
        """Retorna la lista de departamentos de AD requeridos en minúsculas y sin espacios."""
        if not self.departamentos_ad:
            return []
        return [d.strip().lower() for d in self.departamentos_ad.split(',') if d.strip()]

    def get_logo_url(self, request=None):
        """Retorna la URL final del logo, priorizando archivo subido o URL externa."""
        if self.logo_archivo:
            if request:
                return request.build_absolute_uri(self.logo_archivo.url)
            return self.logo_archivo.url
        return self.logo

    def tiene_acceso(self, user):
        """
        Determina si el usuario especificado tiene permisos para visualizar este aplicativo.

        Reglas:
        1. Superusuario: Acceso total e irrestricto a todos los aplicativos.
        2. Sin restricciones (sin grupos AD, sin departamento AD, sin permiso y sin grupos Django):
           Visible para cualquier usuario.
        3. Con restricciones:
           - Si el usuario no está autenticado: denegado (False).
           - Validación Active Directory (AD / LDAP):
               a) Grupos de AD (self.grupos_ad): Compara contra grupos sincronizados en user.profile.ad_groups.
               b) Departamentos de AD (self.departamentos_ad): Compara contra user.profile.department.
           - Validación por permiso_requerido:
               a) user.has_perm(permiso) directo o por grupo Django.
               b) Nombre de grupo Django al que pertenece el usuario.
               c) Nombre de grupo de Active Directory en user.profile.ad_groups.
           - Validación por Grupos de Django (self.grupos M2M): Si pertenece a alguno.
           - Validación por Permisos de Django (self.permisos M2M): Si cuenta con alguno.
        """
        tiene_restriccion = bool(
            self.grupos_ad.strip() or
            self.departamentos_ad.strip() or
            self.permiso_requerido.strip() or
            (self.pk and (self.grupos.exists() or self.permisos.exists()))
        )

        if not tiene_restriccion:
            return True

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        # ----------------------------------------------------------------------
        # 1. Validación directa de Active Directory (AD / LDAP)
        # ----------------------------------------------------------------------
        if hasattr(user, 'profile'):
            profile = user.profile

            # Verificación por grupos corporativos de AD (memberOf sincronizado)
            grupos_ad_req = self.get_grupos_ad_list()
            if grupos_ad_req and profile.ad_groups:
                user_ad_groups = [g.strip().lower() for g in profile.ad_groups.split(',') if g.strip()]
                if any(req in user_ad_groups for req in grupos_ad_req):
                    return True

            # Verificación por departamento de AD
            deptos_ad_req = self.get_departamentos_ad_list()
            if deptos_ad_req and profile.department:
                user_dept = profile.department.strip().lower()
                if user_dept in deptos_ad_req:
                    return True

        # ----------------------------------------------------------------------
        # 2. Validación de permiso_requerido (texto)
        # ----------------------------------------------------------------------
        if self.permiso_requerido.strip():
            req = self.permiso_requerido.strip()

            # Permiso estándar de Django (ej. 'aplicativos.view_crm')
            if '.' in req:
                if user.has_perm(req):
                    return True
            else:
                if user.has_perm(f'aplicativos.{req}') or user.has_perm(req):
                    return True

            # Grupo local de Django
            user_groups = [g.lower() for g in user.groups.values_list('name', flat=True)]
            if req.lower() in user_groups:
                return True

            # Grupo de Active Directory sincronizado en el perfil
            if hasattr(user, 'profile') and user.profile.ad_groups:
                ad_groups = [g.strip().lower() for g in user.profile.ad_groups.split(',') if g.strip()]
                if req.lower() in ad_groups:
                    return True

        # ----------------------------------------------------------------------
        # 3. Validación de Grupos de Django (ManyToMany)
        # ----------------------------------------------------------------------
        if self.pk and self.grupos.exists():
            if self.grupos.filter(id__in=user.groups.all()).exists():
                return True

        # ----------------------------------------------------------------------
        # 4. Validación de Permisos de Django (ManyToMany)
        # ----------------------------------------------------------------------
        if self.pk and self.permisos.exists():
            for p in self.permisos.all():
                perm_codename = f"{p.content_type.app_label}.{p.codename}"
                if user.has_perm(perm_codename):
                    return True

        return False

    def to_dict(self, request=None):
        """Serializa la instancia a un diccionario compatible con JSON."""
        resolved_logo = self.get_logo_url(request=request)
        grupos_list = list(self.grupos.values_list('name', flat=True)) if self.pk else []
        permisos_list = [f"{p.content_type.app_label}.{p.codename}" for p in self.permisos.all()] if self.pk else []

        grupos_ad_list = [g.strip() for g in self.grupos_ad.split(',') if g.strip()] if self.grupos_ad else []
        deptos_ad_list = [d.strip() for d in self.departamentos_ad.split(',') if d.strip()] if self.departamentos_ad else []

        return {
            'id': self.id,
            'nombre': self.nombre,
            'url': self.url,
            'logo': resolved_logo,
            'logo_url': self.logo,
            'logo_archivo': (
                request.build_absolute_uri(self.logo_archivo.url)
                if (self.logo_archivo and request)
                else (self.logo_archivo.url if self.logo_archivo else None)
            ),
            'descripcion': self.descripcion,
            'orden': self.orden,
            'activo': self.activo,
            'grupos_ad': grupos_ad_list,
            'departamentos_ad': deptos_ad_list,
            'permiso_requerido': self.permiso_requerido,
            'grupos': grupos_list,
            'permisos': permisos_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
