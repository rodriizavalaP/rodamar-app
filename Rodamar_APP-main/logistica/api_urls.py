from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()
router.register('buques', api_views.BuqueViewSet, basename='api-buque')
router.register('clientes', api_views.ClienteViewSet, basename='api-cliente')
router.register('camiones', api_views.CamionCiguenaViewSet, basename='api-camion')
router.register('vehiculos', api_views.VehiculoViewSet, basename='api-vehiculo')
router.register('historial', api_views.HistorialEstadoViewSet, basename='api-historial')

urlpatterns = [
    # Endpoint público, sin autenticación: /api/rastreo/<chasis>/
    path('rastreo/<str:chasis>/', api_views.RastreoPublicoAPIView.as_view(), name='api-rastreo'),

    # CRUD REST completo (requiere autenticación): /api/buques/, /api/vehiculos/, etc.
    path('', include(router.urls)),
]
