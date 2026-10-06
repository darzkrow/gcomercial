from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Perfil de usuario extendido para almacenar atributos sincronizados
    desde Active Directory / LDAP.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.CharField('Departamento', max_length=150, blank=True, null=True)
    job_title = models.CharField('Cargo / Título', max_length=150, blank=True, null=True)
    phone = models.CharField('Teléfono', max_length=50, blank=True, null=True)
    ad_dn = models.CharField('Distinguished Name (AD)', max_length=255, blank=True, null=True)
    ad_groups = models.TextField('Grupos de AD', blank=True, null=True, help_text='Grupos de Active Directory sincronizados')
    created_at = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
        ordering = ['user__username']

    def __str__(self):
        return f"Perfil de {self.user.get_full_name() or self.user.username}"
