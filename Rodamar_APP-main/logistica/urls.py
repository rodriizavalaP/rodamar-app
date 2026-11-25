from django.urls import path
from . import views

urlpatterns = [
    path('rastreo/', views.rastreo_vehiculo, name='rastreo'),
    path('panel/', views.dashboard_operaciones, name='dashboard'),
    path('panel/nuevo-vehiculo/', views.registrar_vehiculo, name='registrar_vehiculo'),
    path('panel/nuevo-buque/', views.registrar_buque, name='registrar_buque'),
    path('panel/nuevo-cliente/', views.registrar_cliente, name='registrar_cliente'),
    path('panel/nuevo-camion/', views.registrar_camion, name='registrar_camion'),
    path('panel/actualizar/<int:pk>/', views.actualizar_estado_vehiculo, name='actualizar_estado'),

    # Eliminar (Delete del CRUD)
    path('panel/eliminar-vehiculo/<int:pk>/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
    path('panel/eliminar-buque/<int:pk>/', views.eliminar_buque, name='eliminar_buque'),
    path('panel/eliminar-cliente/<int:pk>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('panel/eliminar-camion/<int:pk>/', views.eliminar_camion, name='eliminar_camion'),

    # Catálogos y edición (Read / Update del CRUD)
    path('gestion/', views.gestion_catalogos, name='gestion'),
    path('panel/editar-vehiculo/<int:pk>/', views.editar_vehiculo, name='editar_vehiculo'),
    path('gestion/editar-buque/<int:pk>/', views.editar_buque, name='editar_buque'),
    path('gestion/editar-cliente/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('gestion/editar-camion/<int:pk>/', views.editar_camion, name='editar_camion'),
]
