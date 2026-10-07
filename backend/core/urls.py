from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Enrutamiento versionado de la API REST según API_PREFIX (ej. 'api/v1/')
    path(settings.API_PREFIX, include('Dashboard.urls')),
    path(settings.API_PREFIX, include('aplicativos.urls')),
]

# Servir archivos multimedia (logos subidos) durante desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
