from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Perfil AD / Información Complementaria'
    verbose_name_plural = 'Perfil AD / Información Complementaria'
    fields = ('department', 'job_title', 'phone', 'ad_groups', 'ad_dn')
    readonly_fields = ('ad_dn', 'ad_groups')


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_department', 'is_staff', 'is_active')

    @admin.display(description='Departamento')
    def get_department(self, obj):
        return obj.profile.department if hasattr(obj, 'profile') else '-'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
