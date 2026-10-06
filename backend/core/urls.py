from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    # Enrutamiento versionado de la API REST según API_PREFIX (ej. 'api/v1/')
    path(settings.API_PREFIX, include('Dashboard.urls')),
]
