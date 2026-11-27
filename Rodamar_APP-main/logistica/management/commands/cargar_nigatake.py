"""Carga la carga del BL 6509749280 para Import Export Nigatake S.R.L.

60 camiones livianos KAMA KMC1042P3 en 20 contenedores (3 por contenedor),
nave MOLLY SCHULTE viaje 150S. Los chasis salen del BL (COSCO) y todos pasan
la validación del dígito verificador del VIN.

Uso:  python manage.py cargar_nigatake
Es seguro repetirlo: no duplica nada.
"""
from datetime import date

from django.core.management.base import BaseCommand

from logistica.models import Buque, Cliente, Contenedor, Vehiculo

# (contenedor, chasis, color)
CARGA = [
    ('CAAU6112141', 'LWU2PM2C3VKM00971', 'Gris'),
    ('CAAU6112141', 'LWU2PM2C2VKM00962', 'Blanco'),
    ('CAAU6112141', 'LWU2PM2C1VKM00922', 'Plata'),
    ('CCLU7913657', 'LWU2PM2C3VKM00954', 'Blanco'),
    ('CCLU7913657', 'LWU2PM2C2VKM00928', 'Plata'),
    ('CCLU7913657', 'LWU2PM2C5VKM00924', 'Plata'),
    ('CSGU6684827', 'LWU2PM2C9VKM00926', 'Plata'),
    ('CSGU6684827', 'LWU2PM2C5VKM00972', 'Gris'),
    ('CSGU6684827', 'LWU2PM2C1VKM00953', 'Blanco'),
    ('CSGU7247380', 'LWU2PM2C2VKM00959', 'Blanco'),
    ('CSGU7247380', 'LWU2PM2C3VKM00937', 'Plata'),
    ('CSGU7247380', 'LWU2PM2C7VKM00942', 'Blanco'),
    ('CSNU6142194', 'LWU2PM2C4VKM00929', 'Plata'),
    ('CSNU6142194', 'LWU2PM2C0VKM00927', 'Plata'),
    ('CSNU6142194', 'LWU2PM2C3VKM00923', 'Plata'),
    ('CSNU7129469', 'LWU2PM2C3VKM00968', 'Blanco'),
    ('CSNU7129469', 'LWU2PM2C1VKM00919', 'Plata'),
    ('CSNU7129469', 'LWU2PM2C6VKM00978', 'Gris'),
    ('CSNU8462350', 'LWU2PM2C4VKM00932', 'Plata'),
    ('CSNU8462350', 'LWU2PM2C7VKM00956', 'Blanco'),
    ('CSNU8462350', 'LWU2PM2C8VKM00951', 'Blanco'),
    ('DFSU7468574', 'LWU2PM2C0VKM00930', 'Plata'),
    ('DFSU7468574', 'LWU2PM2CXVKM00935', 'Plata'),
    ('DFSU7468574', 'LWU2PM2C9VKM00943', 'Blanco'),
    ('FCIU9141822', 'LWU2PM2CXVKM00966', 'Blanco'),
    ('FCIU9141822', 'LWU2PM2C4VKM00977', 'Gris'),
    ('FCIU9141822', 'LWU2PM2C2VKM00976', 'Gris'),
    ('FFAU5563416', 'LWU2PM2C0VKM00944', 'Blanco'),
    ('FFAU5563416', 'LWU2PM2C6VKM00947', 'Blanco'),
    ('FFAU5563416', 'LWU2PM2C8VKM00920', 'Plata'),
    ('FSCU8534681', 'LWU2PM2C6VKM00950', 'Blanco'),
    ('FSCU8534681', 'LWU2PM2C9VKM00957', 'Blanco'),
    ('FSCU8534681', 'LWU2PM2C6VKM00964', 'Blanco'),
    ('GCXU5095228', 'LWU2PM2C4VKM00963', 'Blanco'),
    ('GCXU5095228', 'LWU2PM2CXVKM00949', 'Blanco'),
    ('GCXU5095228', 'LWU2PM2C4VKM00946', 'Blanco'),
    ('GCXU6445090', 'LWU2PM2CXVKM00921', 'Plata'),
    ('GCXU6445090', 'LWU2PM2C0VKM00958', 'Blanco'),
    ('GCXU6445090', 'LWU2PM2C0VKM00961', 'Blanco'),
    ('OOCU6055830', 'LWU2PM2CXVKM00952', 'Blanco'),
    ('OOCU6055830', 'LWU2PM2C5VKM00941', 'Blanco'),
    ('OOCU6055830', 'LWU2PM2C9VKM00974', 'Gris'),
    ('OOLU9745141', 'LWU2PM2C2VKM00945', 'Blanco'),
    ('OOLU9745141', 'LWU2PM2C1VKM00967', 'Blanco'),
    ('OOLU9745141', 'LWU2PM2C7VKM00973', 'Gris'),
    ('OOLU9863226', 'LWU2PM2C8VKM00934', 'Plata'),
    ('OOLU9863226', 'LWU2PM2C8VKM00965', 'Blanco'),
    ('OOLU9863226', 'LWU2PM2C7VKM00925', 'Plata'),
    ('TGBU7418132', 'LWU2PM2C5VKM00955', 'Blanco'),
    ('TGBU7418132', 'LWU2PM2C8VKM00948', 'Blanco'),
    ('TGBU7418132', 'LWU2PM2C0VKM00975', 'Gris'),
    ('TIIU7747688', 'LWU2PM2C6VKM00933', 'Plata'),
    ('TIIU7747688', 'LWU2PM2C5VKM00938', 'Plata'),
    ('TIIU7747688', 'LWU2PM2C2VKM00931', 'Plata'),
    ('TRHU4915822', 'LWU2PM2C5VKM00969', 'Gris'),
    ('TRHU4915822', 'LWU2PM2C7VKM00939', 'Blanco'),
    ('TRHU4915822', 'LWU2PM2C1VKM00970', 'Gris'),
    ('UETU5390053', 'LWU2PM2C3VKM00940', 'Blanco'),
    ('UETU5390053', 'LWU2PM2C9VKM00960', 'Blanco'),
    ('UETU5390053', 'LWU2PM2C1VKM00936', 'Plata'),
]
OBSERVACION = "BL 6509749280 · MOLLY SCHULTE 150S · 40' HDRY · COSCO"


class Command(BaseCommand):
    help = "Carga cliente Nigatake, nave, 20 contenedores y 60 camiones del BL 6509749280."

    def add_arguments(self, parser):
        parser.add_argument('--no-encontrados', action='store_true',
                            help="Deja los 60 camiones en estado 'No encontrado' (aún sin ubicar).")

    def handle(self, *args, **options):
        estado = 'NO_ENCONTRADO'
        cliente, _ = Cliente.objects.get_or_create(
            rut_o_id='NIGATAKE-BO',
            defaults={'nombre_completo': 'Import Export Nigatake S.R.L.'},
        )
        buque, _ = Buque.objects.get_or_create(
            nombre='MOLLY SCHULTE', numero_viaje='150S',
            defaults={'fecha_atraque': date(2026, 11, 19)},
        )
        nuevos = 0
        for numero, chasis, color in CARGA:
            contenedor, _ = Contenedor.objects.get_or_create(
                numero=numero,
                defaults={'fecha_apertura': date(2026, 11, 19), 'observacion': OBSERVACION},
            )
            _, creado = Vehiculo.objects.get_or_create(
                chasis=chasis,
                defaults={
                    'marca': 'KAMA', 'modelo': 'KMC1042P3 (camión liviano)', 'color': color,
                    'buque': buque, 'cliente': cliente, 'contenedor': contenedor,
                    'estado': estado,
                },
            )
            nuevos += creado
            if options['no_encontrados'] and not creado:
                Vehiculo.objects.filter(chasis=chasis, estado='ENCONTRADO', historial__isnull=True).update(estado='NO_ENCONTRADO')
        self.stdout.write(self.style.SUCCESS(
            f"Camiones nuevos: {nuevos} de {len(CARGA)}. Contenedores: {Contenedor.objects.count()}."
        ))
