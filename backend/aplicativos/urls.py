from django.urls import path
from . import views

app_name = 'aplicativos'

urlpatterns = [
    # Colección: Listar aplicativos (GET) y Crear nuevo aplicativo (POST)
    path('aplicativos/', views.api_aplicativos_list_create, name='aplicativos_list_create'),

    # Recurso individual: Obtener detalle (GET), Actualizar (PUT/PATCH) y Eliminar (DELETE)
    path('aplicativos/<int:pk>/', views.api_aplicativo_detail, name='aplicativo_detail'),
]
