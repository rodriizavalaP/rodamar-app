import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistica', '0002_historialestado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='camionciguena',
            name='capacidad',
            field=models.PositiveSmallIntegerField(
                default=8,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(20)],
                verbose_name='Capacidad (vehículos)',
            ),
        ),
        migrations.AddField(
            model_name='historialestado',
            name='camion_ciguena',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='movimientos',
                to='logistica.camionciguena',
            ),
        ),
        migrations.AddField(
            model_name='historialestado',
            name='nota',
            field=models.CharField(blank=True, default='', max_length=160),
        ),
        migrations.CreateModel(
            name='FotoVehiculo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[('LLEGADA', 'Llegada / Descarga'), ('CHEQUEO', 'Chequeo / Inspección'), ('DANO', 'Daño detectado'), ('ENTREGA', 'Entrega / Despacho')],
                    default='LLEGADA', max_length=10)),
                ('descripcion', models.CharField(blank=True, default='', max_length=160)),
                ('imagen', models.BinaryField(editable=False)),
                ('content_type', models.CharField(max_length=30)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='fotos_subidas',
                    to=settings.AUTH_USER_MODEL)),
                ('vehiculo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='fotos',
                    to='logistica.vehiculo')),
            ],
            options={
                'verbose_name': 'Foto de Vehículo',
                'verbose_name_plural': 'Fotos de Vehículos',
                'ordering': ['-fecha'],
            },
        ),
    ]
