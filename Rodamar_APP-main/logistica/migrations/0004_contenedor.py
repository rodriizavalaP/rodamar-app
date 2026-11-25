import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistica', '0003_ciguena_capacidad_fotos'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contenedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(
                    max_length=11, unique=True,
                    validators=[django.core.validators.RegexValidator('^[A-Z]{4}\\d{7}$', 'El número debe tener 4 letras y 7 números (ej: MSKU1234567).')],
                    verbose_name='N° de contenedor')),
                ('sello', models.CharField(blank=True, default='', max_length=40)),
                ('fecha_apertura', models.DateField(blank=True, null=True, verbose_name='Fecha de apertura')),
                ('observacion', models.CharField(blank=True, default='', max_length=160)),
            ],
            options={
                'verbose_name': 'Contenedor',
                'verbose_name_plural': 'Contenedores',
                'ordering': ['-id'],
            },
        ),
        migrations.AddField(
            model_name='vehiculo',
            name='contenedor',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='vehiculos',
                to='logistica.contenedor',
            ),
        ),
    ]
