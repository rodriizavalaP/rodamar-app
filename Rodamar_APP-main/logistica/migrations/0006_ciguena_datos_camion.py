from django.db import migrations, models

from ._seguro import AddFieldSeguro


class Migration(migrations.Migration):

    dependencies = [
        ('logistica', '0005_estado_no_encontrado'),
    ]

    operations = [
        AddFieldSeguro(
            model_name='camionciguena', name='modelo_camion',
            field=models.CharField(blank=True, default='', max_length=60, verbose_name='Marca y modelo del camión'),
        ),
        AddFieldSeguro(
            model_name='camionciguena', name='anio_camion',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Año del camión'),
        ),
    ]
