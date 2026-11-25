from datetime import date

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Buque, Cliente, CamionCiguena, Vehiculo, HistorialEstado


def crear_vehiculo_de_prueba():
    buque = Buque.objects.create(nombre="Glovis Stella", numero_viaje="V-01", fecha_atraque=date.today())
    cliente = Cliente.objects.create(nombre_completo="Automotriz del Norte", rut_o_id="76.111.111-1")
    return Vehiculo.objects.create(
        chasis="TEST123456", marca="Toyota", modelo="Hilux",
        buque=buque, cliente=cliente, estado="ENCONTRADO",
    )


class ModeloVehiculoTest(TestCase):
    def test_str_incluye_chasis_y_modelo(self):
        vehiculo = crear_vehiculo_de_prueba()
        self.assertIn("TEST123456", str(vehiculo))
        self.assertIn("Hilux", str(vehiculo))


class VistaRastreoPublicoTest(TestCase):
    def test_rastreo_sin_login_es_accesible(self):
        response = self.client.get(reverse('rastreo'))
        self.assertEqual(response.status_code, 200)

    def test_rastreo_encuentra_vehiculo_existente(self):
        crear_vehiculo_de_prueba()
        response = self.client.get(reverse('rastreo'), {'chasis': 'TEST123456'})
        self.assertContains(response, "Toyota")

    def test_rastreo_informa_chasis_inexistente(self):
        response = self.client.get(reverse('rastreo'), {'chasis': 'NOEXISTE'})
        # Corregido: coincide con el mensaje de rastreo.html
        self.assertContains(response, "No encontramos coincidencias")


class VistaDashboardPermisosTest(TestCase):
    def setUp(self):
        self.invitado = User.objects.create_user('invitado', password='clave12345')
        self.operador = User.objects.create_user('operador', password='clave12345')
        grupo, _ = Group.objects.get_or_create(name='Operadores')
        self.operador.groups.add(grupo)

    def test_anonimo_no_accede_al_dashboard(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # redirige a login

    def test_usuario_sin_grupo_operadores_no_puede_registrar_vehiculo(self):
        self.client.login(username='invitado', password='clave12345')
        response = self.client.post(reverse('registrar_vehiculo'), {})
        self.assertEqual(response.status_code, 302)  # rebota, no tiene permiso

    def test_operador_si_puede_ver_el_dashboard(self):
        self.client.login(username='operador', password='clave12345')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)


class HistorialEstadoTest(TestCase):
    def setUp(self):
        self.operador = User.objects.create_user('operador2', password='clave12345')
        grupo, _ = Group.objects.get_or_create(name='Operadores')
        self.operador.groups.add(grupo)
        self.vehiculo = crear_vehiculo_de_prueba()
        self.client.login(username='operador2', password='clave12345')

    def test_cambiar_estado_crea_registro_de_historial(self):
        self.client.post(reverse('actualizar_estado', args=[self.vehiculo.pk]), {
            'nuevo_estado': 'EN_PROCESO',
            'ubicacion_patio': 'Bloque A',
        })
        self.assertEqual(HistorialEstado.objects.filter(vehiculo=self.vehiculo).count(), 1)
        historial = HistorialEstado.objects.get(vehiculo=self.vehiculo)
        self.assertEqual(historial.estado_anterior, 'ENCONTRADO')
        self.assertEqual(historial.estado_nuevo, 'EN_PROCESO')


class ApiRestTest(APITestCase):
    """Pruebas de la Unidad 3: CRUD REST, JSON y permisos por rol."""

    def setUp(self):
        self.vehiculo = crear_vehiculo_de_prueba()
        self.invitado = User.objects.create_user('api_invitado', password='clave12345')
        self.operador = User.objects.create_user('api_operador', password='clave12345')
        grupo, _ = Group.objects.get_or_create(name='Operadores')
        self.operador.groups.add(grupo)

    def test_rastreo_publico_api_no_requiere_autenticacion(self):
        url = reverse('api-rastreo', args=['TEST123456'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['chasis'], 'TEST123456')

    def test_listar_vehiculos_requiere_autenticacion(self):
        response = self.client.get('/api/vehiculos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_sin_grupo_no_puede_crear_vehiculo_via_api(self):
        self.client.force_authenticate(user=self.invitado)
        response = self.client.post('/api/vehiculos/', {
            'chasis': 'XYZ999', 'marca': 'Kia', 'modelo': 'Sportage',
            'buque': self.vehiculo.buque_id, 'cliente': self.vehiculo.cliente_id,
            'estado': 'ENCONTRADO',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_operador_si_puede_crear_vehiculo_via_api(self):
        self.client.force_authenticate(user=self.operador)
        response = self.client.post('/api/vehiculos/', {
            'chasis': 'xyz999', 'marca': 'Kia', 'modelo': 'Sportage',
            'buque': self.vehiculo.buque_id, 'cliente': self.vehiculo.cliente_id,
            'estado': 'ENCONTRADO',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['chasis'], 'XYZ999')  # se guarda en mayúsculas

    def test_login_jwt_devuelve_tokens(self):
        response = self.client.post('/api/token/', {
            'username': 'api_operador', 'password': 'clave12345',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class HistorialUbicacionTest(TestCase):
    def setUp(self):
        self.operador = User.objects.create_user('operador_ubicacion', password='clave12345')
        grupo, _ = Group.objects.get_or_create(name='Operadores')
        self.operador.groups.add(grupo)
        self.vehiculo = crear_vehiculo_de_prueba()
        self.client.login(username='operador_ubicacion', password='clave12345')

    def test_cambiar_solo_ubicacion_crea_historial(self):
        self.vehiculo.ubicacion_patio = 'A-01'
        self.vehiculo.save()
        response = self.client.post(reverse('actualizar_estado', args=[self.vehiculo.pk]), {
            'nuevo_estado': 'ENCONTRADO',
            'ubicacion_patio': 'B-15',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(HistorialEstado.objects.filter(vehiculo=self.vehiculo).count(), 1)
        historial = HistorialEstado.objects.get(vehiculo=self.vehiculo)
        self.assertEqual(historial.estado_anterior, 'ENCONTRADO')
        self.assertEqual(historial.estado_nuevo, 'ENCONTRADO')
        self.assertEqual(historial.ubicacion_patio, 'B-15')