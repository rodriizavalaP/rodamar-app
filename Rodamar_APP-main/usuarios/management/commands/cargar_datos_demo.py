from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User

from logistica.models import Buque, Cliente, CamionCiguena, Vehiculo, HistorialEstado


class Command(BaseCommand):
    help = "Carga datos demostrativos de RODAMAR para pruebas y presentación."

    def handle(self, *args, **options):
        # Aseguramos que existan los roles de seguridad.
        clientes_group, _ = Group.objects.get_or_create(name="Clientes")
        Group.objects.get_or_create(name="Operadores")

        # Usuario operador para la demostración. No se reemplaza una cuenta existente.
        operador, creado = User.objects.get_or_create(username="operador_demo")
        if creado:
            operador.set_password("RodamarDemo2026!")
            operador.email = "operador@rodamar.cl"
            operador.save()
        operador.groups.add(Group.objects.get(name="Operadores"))

        # Catálogos demo.
        buques = [
            ("Glovis Stella", "V-001", date.today()),
            ("Pacific Horizon", "V-002", date.today() - timedelta(days=1)),
            ("Ocean Leader", "V-003", date.today() - timedelta(days=2)),
        ]
        buque_objs = []
        for nombre, viaje, fecha in buques:
            obj, _ = Buque.objects.get_or_create(
                nombre=nombre, numero_viaje=viaje, defaults={"fecha_atraque": fecha}
            )
            buque_objs.append(obj)

        clientes = [
            ("Automotriz del Norte", "76.111.111-1"),
            ("Importadora Pacífico", "77.222.222-2"),
            ("Movilidad Chile", "78.333.333-3"),
        ]
        cliente_objs = []
        for nombre, rut in clientes:
            obj, _ = Cliente.objects.get_or_create(
                rut_o_id=rut, defaults={"nombre_completo": nombre, "email": "contacto@rodamar.cl"}
            )
            cliente_objs.append(obj)

        camiones = [
            ("ABCD12", "Transportes Portuarios SpA", "Carlos Soto"),
            ("EFGH34", "Logística del Pacífico", "María González"),
            ("IJKL56", "Cargas Chile", "Pedro Rojas"),
        ]
        camion_objs = []
        for patente, empresa, chofer in camiones:
            obj, _ = CamionCiguena.objects.get_or_create(
                patente=patente,
                defaults={"empresa_transporte": empresa, "nombre_chofer": chofer},
            )
            camion_objs.append(obj)

        vehiculos = [
            ("ROD-DEMO-001", "Toyota", "Corolla", "Blanco", "A-01", "ENCONTRADO"),
            ("ROD-DEMO-002", "Kia", "Sportage", "Gris", "A-02", "EN_PROCESO"),
            ("ROD-DEMO-003", "Hyundai", "Tucson", "Negro", "A-03", "EN_CAMINO"),
            ("ROD-DEMO-004", "Mazda", "CX-5", "Rojo", "B-01", "ENTREGADO"),
            ("ROD-DEMO-005", "Nissan", "Qashqai", "Azul", "B-02", "EN_PROCESO"),
            ("ROD-DEMO-006", "Toyota", "Hilux", "Plata", "B-03", "ENCONTRADO"),
            ("ROD-DEMO-007", "Suzuki", "Vitara", "Blanco", "C-01", "EN_CAMINO"),
            ("ROD-DEMO-008", "MG", "ZS", "Negro", "C-02", "EN_PROCESO"),
            ("ROD-DEMO-009", "Ford", "Ranger", "Gris", "C-03", "ENTREGADO"),
            ("ROD-DEMO-010", "Chevrolet", "Tracker", "Verde", "D-01", "ENCONTRADO"),
        ]

        creados = 0
        for i, (chasis, marca, modelo, color, ubicacion, estado) in enumerate(vehiculos):
            vehiculo, creado = Vehiculo.objects.get_or_create(
                chasis=chasis,
                defaults={
                    "marca": marca,
                    "modelo": modelo,
                    "color": color,
                    "ubicacion_patio": ubicacion,
                    "estado": estado,
                    "buque": buque_objs[i % len(buque_objs)],
                    "cliente": cliente_objs[i % len(cliente_objs)],
                    "camion_ciguena": camion_objs[i % len(camion_objs)],
                },
            )
            if creado:
                creados += 1
                HistorialEstado.objects.create(
                    vehiculo=vehiculo,
                    estado_anterior=None,
                    estado_nuevo=vehiculo.estado,
                    ubicacion_patio=vehiculo.ubicacion_patio,
                    usuario=operador,
                )

        self.stdout.write(self.style.SUCCESS(
            f"Datos demo cargados: {len(buque_objs)} buques, {len(cliente_objs)} clientes, "
            f"{len(camion_objs)} camiones y {creados} vehículos nuevos."
        ))
        self.stdout.write("Usuario demo operador: operador_demo / RodamarDemo2026!")
