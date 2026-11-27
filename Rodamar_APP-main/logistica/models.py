from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models

# Tabla 1: Buque que arriba al puerto
class Buque(models.Model):
    # Nombre de la nave (ej. Glovis Stella)
    nombre = models.CharField(max_length=120)
    # Código o número de viaje que hace el barco
    numero_viaje = models.CharField(max_length=60)
    # Fecha exacta en que atraca en el muelle
    fecha_atraque = models.DateField()

    def __str__(self):
        return f"{self.nombre} (Viaje: {self.numero_viaje})"


# Tabla 2: Cliente o empresa dueña de los vehículos
class Cliente(models.Model):
    # Razón Social o Nombre del consignatario
    nombre_completo = models.CharField(max_length=150)
    # RUT o Identificador único (no repetible)
    rut_o_id = models.CharField(max_length=20, unique=True)
    # Datos de contacto
    telefono = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre_completo} - {self.rut_o_id}"


# Tabla 3: Camión Cigueña / Transporte Terrestre
class CamionCiguena(models.Model):
    patente = models.CharField(max_length=20, unique=True, verbose_name="Patente Camión")
    empresa_transporte = models.CharField(max_length=100)
    nombre_chofer = models.CharField(max_length=120, blank=True, null=True)
    rut_chofer = models.CharField(max_length=20, blank=True, null=True)
    # Cuántos vehículos puede llevar en un mismo viaje
    capacidad = models.PositiveSmallIntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name="Capacidad (vehículos)",
    )

    def __str__(self):
        return f"Cigueña: {self.patente} ({self.empresa_transporte})"

    @property
    def cupos_libres(self):
        return max(self.capacidad - self.vehiculos_cargados.count(), 0)


# Tabla 4: Vehículos que se descargan en el puerto
class Vehiculo(models.Model):
    ESTADOS = [
        ('NO_ENCONTRADO', '0. No encontrado (aún sin ubicar)'),
        ('ENCONTRADO', '1. Descarga / Encontrado'),
        ('EN_PROCESO', '2. Inspección / En Proceso'),
        ('EN_CAMINO', '3. En Traslado / Faena'),
        ('ENTREGADO', '4. Entregado / Despachado'),
    ]

    chasis = models.CharField(max_length=50, unique=True, verbose_name="VIN / Chasis")
    marca = models.CharField(max_length=60)
    modelo = models.CharField(max_length=60)
    color = models.CharField(max_length=40, blank=True, null=True)
    ubicacion_patio = models.CharField(max_length=60, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ENCONTRADO')
    
    # Relaciones del vehículo
    buque = models.ForeignKey(Buque, on_delete=models.CASCADE, related_name='vehiculos')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='vehiculos')
    camion_ciguena = models.ForeignKey(
        CamionCiguena, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='vehiculos_cargados'
    )
    
    # Algunos vehículos llegan dentro de un contenedor (se anota su número)
    contenedor = models.ForeignKey(
        'Contenedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehiculos'
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.chasis} - {self.marca} {self.modelo}"


# Tabla 5: Historial de trazabilidad de cada vehículo
# Cada vez que un vehículo cambia de estado o de ubicación en patio,
# queda un registro permanente aquí. Esto es lo que le da a RODAMAR la
# trazabilidad "en tiempo real" que promete el proyecto: sin esta tabla
# solo se conoce el estado actual, pero se pierde el historial de cuándo
# y quién hizo cada movimiento.
class HistorialEstado(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='historial')
    estado_anterior = models.CharField(max_length=20, choices=Vehiculo.ESTADOS, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=20, choices=Vehiculo.ESTADOS)
    ubicacion_patio = models.CharField(max_length=60, blank=True, null=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_registrados'
    )
    # Si el movimiento fue una asignación/retiro de cigüeña, queda registrado aquí
    camion_ciguena = models.ForeignKey(
        CamionCiguena,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos'
    )
    nota = models.CharField(max_length=160, blank=True, default='')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Historial de Estado"
        verbose_name_plural = "Historial de Estados"

    def __str__(self):
        return f"{self.vehiculo.chasis}: {self.estado_anterior or '—'} → {self.estado_nuevo} ({self.fecha:%d-%m-%Y %H:%M})"


# Tabla 6: Fotos del chequeo de cada vehículo (cómo llegó, daños, etc.)
# La imagen se guarda en la propia base de datos para que funcione igual en
# local y en la nube (Vercel no permite guardar archivos en disco).
class FotoVehiculo(models.Model):
    TIPOS = [
        ('LLEGADA', 'Llegada / Descarga'),
        ('CHEQUEO', 'Chequeo / Inspección'),
        ('DANO', 'Daño detectado'),
        ('ENTREGA', 'Entrega / Despacho'),
    ]

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='fotos')
    tipo = models.CharField(max_length=10, choices=TIPOS, default='LLEGADA')
    descripcion = models.CharField(max_length=160, blank=True, default='')
    imagen = models.BinaryField(editable=False)
    content_type = models.CharField(max_length=30)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fotos_subidas'
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Foto de Vehículo"
        verbose_name_plural = "Fotos de Vehículos"

    def __str__(self):
        return f"{self.vehiculo.chasis} - {self.get_tipo_display()} ({self.fecha:%d-%m-%Y})"


# Tabla 7: Contenedor en el que llegan algunos vehículos
class Contenedor(models.Model):
    numero = models.CharField(
        max_length=11,
        unique=True,
        validators=[RegexValidator(
            r'^[A-Z]{4}\d{7}$',
            'El número debe tener 4 letras y 7 números (ej: MSKU1234567).'
        )],
        verbose_name="N° de contenedor",
    )
    sello = models.CharField(max_length=40, blank=True, default='')
    fecha_apertura = models.DateField(null=True, blank=True, verbose_name="Fecha de apertura")
    observacion = models.CharField(max_length=160, blank=True, default='')

    class Meta:
        ordering = ['-id']
        verbose_name = "Contenedor"
        verbose_name_plural = "Contenedores"

    def __str__(self):
        return self.numero
