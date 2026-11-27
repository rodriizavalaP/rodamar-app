"""Carga las 5 cigüeñas (camiones) de los MIC/DTA del BL 6509749280 y les asigna sus 30 camionetas KAMA.

Datos: patente, empresa, marca/modelo y año del camión, conductor y su documento, N° de MIC,
y los últimos 5 dígitos del chasis (VKM00xxx) de las 6 camionetas que lleva cada uno.

Uso:  python manage.py cargar_ciguenas_nigatake      (requiere haber corrido antes cargar_nigatake)
Es seguro repetirlo.
"""
from django.core.management.base import BaseCommand

from logistica.models import CamionCiguena, HistorialEstado, Vehiculo

# (patente, empresa, modelo del camión, año, conductor, documento, N° MIC, serie de los 6 chasis)
CAMIONES = [
    ('4082PKT', 'TRANSPORTES TRANS PLAYERS SRL', 'INTERNATIONAL', 2011, 'RENE QUISPE', 'CI 4956244', '26CL958849D', [933, 931, 955, 967, 945, 973]),
    ('2470FIN', 'TRANSPORTES TRANS PLAYERS SRL', 'VOLVO', 2004, 'REYNALDO SURI PONGO', 'CI 4952770', '26CL958847B', [964, 974, 975, 961, 941, 952]),
    ('2420BDE', 'TRANSPORTES TRANS PLAYERS SRL', 'VOLVO', 2002, 'REYNALDO VARGAS MAMANI', 'CI 6010173', '26CL958809W', [923, 968, 978, 943, 957, 950]),
    ('5241CEN', 'TRANSPORTES VILLCATRUCKS LOGISTIC S.R.L.', 'VOLVO', 2014, 'JUAN CARLOS APAZA CONDORI', 'CI 8361524', '26CL955744R', [925, 938, 969, 970, 977, 966]),
    ('4458GLB', 'TRANSPORTES VILLCATRUCKS LOGISTIC S.R.L.', 'VOLVO', 2011, 'JOSE MIGUEL VILLCA OJEDA', 'CI 3559966', '26CL955531L', [949, 963, 946, 958, 921, 934]),
]


class Command(BaseCommand):
    help = "Carga las cigüeñas de Nigatake y asigna las camionetas a cada una."

    def handle(self, *args, **options):
        asignados = faltantes = 0
        for patente, empresa, modelo, anio, chofer, doc, mic, series in CAMIONES:
            camion, _ = CamionCiguena.objects.update_or_create(
                patente=patente,
                defaults={
                    'empresa_transporte': empresa, 'modelo_camion': modelo, 'anio_camion': anio,
                    'nombre_chofer': chofer, 'rut_chofer': doc, 'capacidad': len(series),
                },
            )
            for serie in series:
                v = Vehiculo.objects.filter(chasis__endswith='VKM%05d' % serie).first()
                if v is None:
                    faltantes += 1
                    self.stdout.write(self.style.WARNING(f"No existe la camioneta ...VKM{serie:05d} (¿corriste cargar_nigatake?)"))
                    continue
                if v.camion_ciguena_id != camion.pk:
                    v.camion_ciguena = camion
                    v.save()
                    HistorialEstado.objects.create(
                        vehiculo=v, estado_anterior=v.estado, estado_nuevo=v.estado,
                        ubicacion_patio=v.ubicacion_patio, camion_ciguena=camion,
                        nota=f"Asignado a la cigüeña {patente} · MIC {mic}",
                    )
                    asignados += 1
        self.stdout.write(self.style.SUCCESS(
            f"Cigüeñas: {len(CAMIONES)}. Camionetas asignadas ahora: {asignados}. No encontradas: {faltantes}."
        ))
