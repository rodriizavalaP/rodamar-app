from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Buque, Cliente, CamionCiguena, Vehiculo, HistorialEstado
from .permissions import EsOperadorOSoloLectura
from .serializers import (
    BuqueSerializer,
    ClienteSerializer,
    CamionCiguenaSerializer,
    VehiculoSerializer,
    VehiculoPublicoSerializer,
    HistorialEstadoSerializer,
)


class BuqueViewSet(viewsets.ModelViewSet):
    """CRUD REST completo de Buques: /api/buques/"""
    queryset = Buque.objects.all().order_by('-fecha_atraque')
    serializer_class = BuqueSerializer
    permission_classes = [EsOperadorOSoloLectura]


class ClienteViewSet(viewsets.ModelViewSet):
    """CRUD REST completo de Clientes: /api/clientes/"""
    queryset = Cliente.objects.all().order_by('nombre_completo')
    serializer_class = ClienteSerializer
    permission_classes = [EsOperadorOSoloLectura]


class CamionCiguenaViewSet(viewsets.ModelViewSet):
    """CRUD REST completo de Camiones Cigüeña: /api/camiones/"""
    queryset = CamionCiguena.objects.all().order_by('patente')
    serializer_class = CamionCiguenaSerializer
    permission_classes = [EsOperadorOSoloLectura]


class VehiculoViewSet(viewsets.ModelViewSet):
    """
    CRUD REST completo de Vehículos: /api/vehiculos/
    Soporta filtro simple por query param, ej: /api/vehiculos/?estado=EN_PROCESO
    """
    serializer_class = VehiculoSerializer
    permission_classes = [EsOperadorOSoloLectura]

    def get_queryset(self):
        queryset = Vehiculo.objects.all().select_related('buque', 'cliente', 'camion_ciguena')
        estado = self.request.query_params.get('estado')
        chasis = self.request.query_params.get('chasis')
        if estado:
            queryset = queryset.filter(estado=estado)
        if chasis:
            queryset = queryset.filter(chasis__icontains=chasis)
        return queryset.order_by('-fecha_registro')

    def perform_update(self, serializer):
        # Cada vez que se actualiza un vehículo vía API (ej. cambio de
        # estado desde una app externa autenticada), queda registrado en
        # el historial de trazabilidad, igual que en el panel HTML.
        vehiculo_anterior = self.get_object()
        estado_anterior = vehiculo_anterior.estado
        ubicacion_anterior = vehiculo_anterior.ubicacion_patio or ''
        instancia = serializer.save()
        cambio_estado = instancia.estado != estado_anterior
        cambio_ubicacion = (instancia.ubicacion_patio or '') != ubicacion_anterior
        if cambio_estado or cambio_ubicacion:
            HistorialEstado.objects.create(
                vehiculo=instancia,
                estado_anterior=estado_anterior,
                estado_nuevo=instancia.estado,
                ubicacion_patio=instancia.ubicacion_patio,
                usuario=self.request.user if self.request.user.is_authenticated else None,
            )

    def perform_create(self, serializer):
        instancia = serializer.save()
        HistorialEstado.objects.create(
            vehiculo=instancia,
            estado_anterior=None,
            estado_nuevo=instancia.estado,
            ubicacion_patio=instancia.ubicacion_patio,
            usuario=self.request.user if self.request.user.is_authenticated else None,
        )


class HistorialEstadoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Solo lectura: /api/historial/ — el historial se genera automáticamente
    al crear/actualizar vehículos, nunca se edita a mano.
    """
    serializer_class = HistorialEstadoSerializer
    permission_classes = [EsOperadorOSoloLectura]

    def get_queryset(self):
        queryset = HistorialEstado.objects.all().select_related('vehiculo', 'usuario')
        vehiculo_id = self.request.query_params.get('vehiculo')
        if vehiculo_id:
            queryset = queryset.filter(vehiculo_id=vehiculo_id)
        return queryset


class RastreoPublicoAPIView(APIView):
    """
    Endpoint público (sin login) para consultar el estado de un vehículo
    por su VIN/chasis en JSON: GET /api/rastreo/<chasis>/
    Es la versión API de la vista HTML `rastreo_vehiculo`, pensada para
    que la consuma una app móvil o un tercero (ej. el cliente naviero).
    """
    permission_classes = [AllowAny]

    def get(self, request, chasis):
        try:
            vehiculo = Vehiculo.objects.select_related('buque', 'cliente').get(chasis__iexact=chasis.strip())
        except Vehiculo.DoesNotExist:
            return Response(
                {'detail': f"No se encontró ningún vehículo con el chasis '{chasis}'."},
                status=404,
            )
        serializer = VehiculoPublicoSerializer(vehiculo)
        return Response(serializer.data)
