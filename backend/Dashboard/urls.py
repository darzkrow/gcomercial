from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Monitoreo de Salud
    path('health/', views.api_health, name='api_health'),

    # Autenticación y Sesión
    path('auth/login/', views.api_login, name='api_login'),
    path('auth/logout/', views.api_logout, name='api_logout'),
    path('auth/me/', views.api_me, name='api_me'),
    path('auth/refresh/', views.api_refresh_token, name='api_refresh_token'),

    # Perfil de Usuario
    path('profile/', views.api_profile, name='api_profile'),

    # Métricas y Dashboard
    path('dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('users/', views.api_users_list, name='api_users_list'),
]
