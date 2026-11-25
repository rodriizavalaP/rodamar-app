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


class SeguridadYCrudWebTest(TestCase):
    def setUp(self):
        self.operador = User.objects.create_user('op_web', password='clave12345')
        self.operador.groups.add(Group.objects.get_or_create(name='Operadores')[0])
        self.cliente_user = User.objects.create_user('cli_web', password='clave12345')
        self.cliente_user.groups.add(Group.objects.get_or_create(name='Clientes')[0])
        self.vehiculo = crear_vehiculo_de_prueba()

    def test_cliente_registrado_no_ve_el_panel(self):
        self.client.login(username='cli_web', password='clave12345')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('rastreo'))

    def test_cliente_registrado_no_accede_a_gestion_ni_edicion(self):
        self.client.login(username='cli_web', password='clave12345')
        self.assertEqual(self.client.get(reverse('gestion')).status_code, 302)
        self.assertEqual(self.client.get(reverse('editar_vehiculo', args=[self.vehiculo.pk])).status_code, 302)

    def test_rastreo_publico_no_muestra_rut_del_cliente(self):
        response = self.client.get(reverse('rastreo'), {'chasis': 'TEST123456'})
        self.assertNotContains(response, '76.111.111-1')

    def test_busqueda_por_rut_no_funciona_para_anonimos(self):
        response = self.client.get(reverse('rastreo'), {'codigo': '76.111.111-1'})
        self.assertNotContains(response, 'TEST123456')

    def test_operador_edita_cliente(self):
        self.client.login(username='op_web', password='clave12345')
        cliente = self.vehiculo.cliente
        response = self.client.post(reverse('editar_cliente', args=[cliente.pk]), {
            'nombre_completo': 'Nombre Nuevo', 'rut_o_id': cliente.rut_o_id,
            'telefono': '', 'email': '',
        })
        self.assertEqual(response.status_code, 302)
        cliente.refresh_from_db()
        self.assertEqual(cliente.nombre_completo, 'Nombre Nuevo')

    def test_edicion_invalida_muestra_errores_y_no_guarda(self):
        self.client.login(username='op_web', password='clave12345')
        cliente = self.vehiculo.cliente
        response = self.client.post(reverse('editar_cliente', args=[cliente.pk]), {
            'nombre_completo': '', 'rut_o_id': cliente.rut_o_id,
        })
        self.assertEqual(response.status_code, 200)
        cliente.refresh_from_db()
        self.assertEqual(cliente.nombre_completo, 'Automotriz del Norte')

    def test_editar_vehiculo_cambiando_estado_crea_historial(self):
        self.client.login(username='op_web', password='clave12345')
        v = self.vehiculo
        response = self.client.post(reverse('editar_vehiculo', args=[v.pk]), {
            'chasis': v.chasis, 'marca': 'Toyota', 'modelo': 'Hilux', 'color': 'Rojo',
            'buque': v.buque_id, 'cliente': v.cliente_id, 'camion_ciguena': '',
            'estado': 'EN_PROCESO', 'ubicacion_patio': 'C-03',
        })
        self.assertEqual(response.status_code, 302)
        h = HistorialEstado.objects.get(vehiculo=v)
        self.assertEqual(h.estado_anterior, 'ENCONTRADO')
        self.assertEqual(h.estado_nuevo, 'EN_PROCESO')

    def test_operador_elimina_buque_desde_gestion(self):
        self.client.login(username='op_web', password='clave12345')
        response = self.client.post(reverse('eliminar_buque', args=[self.vehiculo.buque_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Buque.objects.exists())

    def test_usuario_cliente_no_lee_api_de_clientes(self):
        from rest_framework.test import APIClient
        api = APIClient()
        api.force_authenticate(user=self.cliente_user)
        self.assertEqual(api.get('/api/clientes/').status_code, 403)
