from django.contrib import admin
from .models import Buque, Cliente, CamionCiguena, Vehiculo, HistorialEstado


@admin.register(Buque)
class BuqueAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'numero_viaje', 'fecha_atraque')
    search_fields = ('nombre', 'numero_viaje')
    list_filter = ('fecha_atraque',)
    ordering = ('-fecha_atraque',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rut_o_id', 'telefono', 'email')
    search_fields = ('nombre_completo', 'rut_o_id', 'email')


@admin.register(CamionCiguena)
class CamionCiguenaAdmin(admin.ModelAdmin):
    list_display = ('patente', 'empresa_transporte', 'nombre_chofer', 'rut_chofer')
    search_fields = ('patente', 'empresa_transporte', 'nombre_chofer')
    list_filter = ('empresa_transporte',)


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('chasis', 'marca', 'modelo', 'estado', 'ubicacion_patio', 'buque', 'cliente', 'fecha_registro')
    search_fields = ('chasis', 'marca', 'modelo')
    list_filter = ('estado', 'buque', 'marca')
    date_hierarchy = 'fecha_registro'


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'estado_anterior', 'estado_nuevo', 'ubicacion_patio', 'usuario', 'fecha')
    list_filter = ('estado_nuevo', 'fecha')
    search_fields = ('vehiculo__chasis',)
    # El historial se genera automáticamente desde las vistas/API,
    # no tiene sentido crearlo ni editarlo a mano desde el Admin.
    readonly_fields = ('vehiculo', 'estado_anterior', 'estado_nuevo', 'ubicacion_patio', 'usuario', 'fecha')

    def has_add_permission(self, request):
        return False
