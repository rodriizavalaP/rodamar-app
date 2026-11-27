from django.db import migrations, models

ESTADOS = [('NO_ENCONTRADO', '0. No encontrado (aún sin ubicar)'), ('ENCONTRADO', '1. Descarga / Encontrado'), ('EN_PROCESO', '2. Inspección / En Proceso'), ('EN_CAMINO', '3. En Traslado / Faena'), ('ENTREGADO', '4. Entregado / Despachado')]


class Migration(migrations.Migration):
    """Todo vehículo nuevo parte en el estado 0 (No encontrado). No toca datos existentes."""

    dependencies = [
        ('logistica', '0006_ciguena_datos_camion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehiculo', name='estado',
            field=models.CharField(choices=ESTADOS, default='NO_ENCONTRADO', max_length=20),
        ),
    ]
