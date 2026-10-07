from django.contrib import admin
from .models import Aplicativo


@admin.register(Aplicativo)
class AplicativoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'url',
        'grupos_ad_display',
        'departamentos_ad_display',
        'permiso_requerido',
        'logo_display',
        'orden',
        'activo',
        'updated_at'
    )
    list_display_links = ('id', 'nombre')
    list_filter = ('activo', 'grupos', 'created_at', 'updated_at')
    search_fields = ('nombre', 'url', 'descripcion', 'grupos_ad', 'departamentos_ad', 'permiso_requerido')
    list_editable = ('orden', 'activo')
    ordering = ('orden', 'nombre')
    filter_horizontal = ('grupos', 'permisos')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Información Principal', {
            'fields': ('nombre', 'url', 'descripcion')
        }),
        ('Control de Acceso Active Directory (AD / LDAP)', {
            'fields': ('grupos_ad', 'departamentos_ad'),
            'description': (
                'Configure los grupos de seguridad y departamentos corporativos sincronizados desde Active Directory / LDAP. '
                'Los usuarios autenticados con AD cuyos grupos o departamento coincidan tendrán acceso automático al aplicativo.'
            )
        }),
        ('Control de Acceso Local / Django', {
            'fields': ('permiso_requerido', 'grupos', 'permisos'),
            'classes': ('collapse',),
            'description': (
                'Configuración opcional para permisos de Django o grupos locales. '
                'Si se deja todo en blanco, el aplicativo será público para todos los usuarios.'
            )
        }),
        ('Recursos Visuales', {
            'fields': ('logo', 'logo_archivo'),
            'description': 'Puede ingresar una URL de imagen externa o subir un archivo local.'
        }),
        ('Configuración y Estado', {
            'fields': ('orden', 'activo', 'created_at', 'updated_at')
        }),
    )

    def logo_display(self, obj):
        logo_url = obj.get_logo_url()
        if logo_url:
            return logo_url[:35] + '...' if len(logo_url) > 35 else logo_url
        return '-'
    logo_display.short_description = 'Logo'

    def grupos_ad_display(self, obj):
        return obj.grupos_ad[:35] + '...' if len(obj.grupos_ad) > 35 else (obj.grupos_ad or '-')
    grupos_ad_display.short_description = 'Grupos AD'

    def departamentos_ad_display(self, obj):
        return obj.departamentos_ad or '-'
    departamentos_ad_display.short_description = 'Depto. AD'
