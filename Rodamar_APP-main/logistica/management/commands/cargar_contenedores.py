"""Carga los 20 contenedores del BL 6509749280 (nave MOLLY SCHULTE, viaje 150S).

Uso:  python manage.py cargar_contenedores
Es seguro repetirlo: no duplica los que ya existen.
"""
from datetime import date

from django.core.management.base import BaseCommand

from logistica.models import Contenedor

NUMEROS = [
    'CAAU6112141', 'CCLU7913657', 'CSGU6684827', 'CSGU7247380', 'CSNU6142194',
    'CSNU7129469', 'UETU5390053', 'TGBU7418132', 'GCXU6445090', 'OOCU6055830',
    'OOLU9745141', 'OOLU9863226', 'TIIU7747688', 'TRHU4915822', 'CSNU8462350',
    'DFSU7468574', 'FCIU9141822', 'FFAU5563416', 'FSCU8534681', 'GCXU5095228',
]
OBSERVACION = "BL 6509749280 · MOLLY SCHULTE 150S · 40' HDRY · COSCO"


class Command(BaseCommand):
    help = "Carga los contenedores del BL 6509749280 (MOLLY SCHULTE 150S)."

    def handle(self, *args, **options):
        creados = 0
        for numero in NUMEROS:
            _, nuevo = Contenedor.objects.get_or_create(
                numero=numero,
                defaults={'fecha_apertura': date(2026, 11, 26), 'observacion': OBSERVACION},
            )
            creados += nuevo
        self.stdout.write(self.style.SUCCESS(
            f"Contenedores nuevos: {creados}. Ya existían: {len(NUMEROS) - creados}."
        ))
