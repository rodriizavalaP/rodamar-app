from rest_framework import serializers

from .models import Buque, Cliente, CamionCiguena, Vehiculo, HistorialEstado


class BuqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buque
        fields = ['id', 'nombre', 'numero_viaje', 'fecha_atraque']


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre_completo', 'rut_o_id', 'telefono', 'email']


class CamionCiguenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CamionCiguena
        fields = ['id', 'patente', 'empresa_transporte', 'nombre_chofer', 'rut_chofer']


class HistorialEstadoSerializer(serializers.ModelSerializer):
    estado_anterior_display = serializers.CharField(source='get_estado_anterior_display', read_only=True)
    estado_nuevo_display = serializers.CharField(source='get_estado_nuevo_display', read_only=True)
    usuario = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = HistorialEstado
        fields = [
            'id', 'vehiculo', 'estado_anterior', 'estado_anterior_display',
            'estado_nuevo', 'estado_nuevo_display', 'ubicacion_patio',
            'usuario', 'fecha',
        ]
        read_only_fields = ['fecha']


class VehiculoSerializer(serializers.ModelSerializer):
    """Serializer completo, para uso interno (operadores autenticados)."""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    buque_nombre = serializers.CharField(source='buque.nombre', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    camion_patente = serializers.CharField(source='camion_ciguena.patente', read_only=True, default=None)

    class Meta:
        model = Vehiculo
        fields = [
            'id', 'chasis', 'marca', 'modelo', 'color',
            'ubicacion_patio', 'estado', 'estado_display',
            'buque', 'buque_nombre', 'cliente', 'cliente_nombre',
            'camion_ciguena', 'camion_patente', 'fecha_registro',
        ]
        read_only_fields = ['fecha_registro']

    def validate_chasis(self, value):
        # Regla de negocio simple: el VIN siempre se guarda en mayúsculas
        # para que el rastreo público (que usa __iexact) sea consistente.
        return value.strip().upper()


class VehiculoPublicoSerializer(serializers.ModelSerializer):
    """
    Serializer reducido para el endpoint público de rastreo.
    Deliberadamente NO expone datos sensibles del cliente (RUT, teléfono,
    email) ni del chofer/cigüeña: cualquiera con el VIN puede consultar
    esto sin autenticarse, así que solo va lo que necesita ver un
    consignatario o transportista externo.
    """
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    buque = serializers.CharField(source='buque.nombre', read_only=True)
    numero_viaje = serializers.CharField(source='buque.numero_viaje', read_only=True)

    class Meta:
        model = Vehiculo
        fields = [
            'chasis', 'marca', 'modelo', 'color',
            'estado', 'estado_display', 'ubicacion_patio',
            'buque', 'numero_viaje',
        ]
