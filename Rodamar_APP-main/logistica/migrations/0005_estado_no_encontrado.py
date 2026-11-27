from django.db import migrations, models

ESTADOS = [('NO_ENCONTRADO', '0. No encontrado (aún sin ubicar)'), ('ENCONTRADO', '1. Descarga / Encontrado'), ('EN_PROCESO', '2. Inspección / En Proceso'), ('EN_CAMINO', '3. En Traslado / Faena'), ('ENTREGADO', '4. Entregado / Despachado')]


class Migration(migrations.Migration):
    """Agrega el estado NO_ENCONTRADO (solo cambia las opciones; no toca las tablas)."""

    dependencies = [
        ('logistica', '0004_contenedor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehiculo', name='estado',
            field=models.CharField(choices=ESTADOS, default='ENCONTRADO', max_length=20),
        ),
        migrations.AlterField(
            model_name='historialestado', name='estado_anterior',
            field=models.CharField(blank=True, choices=ESTADOS, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='historialestado', name='estado_nuevo',
            field=models.CharField(choices=ESTADOS, max_length=20),
        ),
    ]
