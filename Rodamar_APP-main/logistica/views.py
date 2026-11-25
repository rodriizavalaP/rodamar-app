from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Vehiculo, Buque, Cliente, CamionCiguena, HistorialEstado
from .forms import VehiculoForm, BuqueForm, ClienteForm, CamionCiguenaForm


def es_operador(user):
    """
    Solo superusuarios o miembros del grupo 'Operadores' (el que se
    asigna automáticamente al registrarse, ver usuarios/views.py) pueden
    escribir en el panel. Cualquier otro usuario autenticado solo puede
    ver el dashboard, no modificarlo.
    """
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Operadores').exists())


# Decorador combinado: exige login Y pertenecer al grupo Operadores.
solo_operadores = user_passes_test(es_operador, login_url='login')


# Vista pública: Rastreo por Chasis (VIN) individual o Flota por RUT / Empresa
def rastreo_vehiculo(request):
    # Lee 'codigo' o 'chasis' para compatibilidad con cualquier enlace
    query = (request.GET.get('codigo') or request.GET.get('chasis') or '').strip()
    
    vehiculo = None
    vehiculos_empresa = None
    cliente_encontrado = None
    historial = None
    mensaje_error = None

    if query:
        # 1. Búsqueda directa por número de chasis (VIN) exacto
        vehiculo = Vehiculo.objects.select_related('buque', 'cliente', 'camion_ciguena').filter(chasis__iexact=query).first()

        if vehiculo:
            historial = vehiculo.historial.all()
        else:
            # 2. Si no es chasis, verifica si coincide con el RUT o Nombre de un Cliente/Empresa
            clientes = Cliente.objects.filter(
                Q(rut_o_id__iexact=query) | Q(nombre_completo__icontains=query)
            )
            if clientes.exists():
                cliente_encontrado = clientes.first()
                vehiculos_empresa = Vehiculo.objects.filter(cliente=cliente_encontrado).select_related('buque', 'camion_ciguena')
            else:
                # 3. Búsqueda flexible parcial
                coincidencias = Vehiculo.objects.filter(
                    Q(chasis__icontains=query) |
                    Q(cliente__nombre_completo__icontains=query) |
                    Q(cliente__rut_o_id__icontains=query)
                ).select_related('buque', 'cliente', 'camion_ciguena')

                if coincidencias.exists():
                    vehiculos_empresa = coincidencias
                else:
                    mensaje_error = f"No se encontraron vehículos asociados al chasis o cliente '{query}'."

    return render(request, 'logistica/rastreo.html', {
        'vehiculo': vehiculo,
        'historial': historial,
        'vehiculos_empresa': vehiculos_empresa,
        'cliente_encontrado': cliente_encontrado,
        'termino': query,
        'query': query,
        'mensaje_error': mensaje_error
    })


# Vista privada: Panel operativo para el operador
@login_required
def dashboard_operaciones(request):
    q = request.GET.get('q', '').strip()
    filtro_estado = request.GET.get('estado', '')
    
    vehiculos = Vehiculo.objects.all().select_related('buque', 'cliente', 'camion_ciguena')
    if q:
        vehiculos = vehiculos.filter(
            Q(chasis__icontains=q) |
            Q(marca__icontains=q) |
            Q(modelo__icontains=q) |
            Q(cliente__nombre_completo__icontains=q)
        )
    if filtro_estado:
        vehiculos = vehiculos.filter(estado=filtro_estado)

    # Contadores de métricas
    total = Vehiculo.objects.count()
    encontrados = Vehiculo.objects.filter(estado='ENCONTRADO').count()
    en_proceso = Vehiculo.objects.filter(estado='EN_PROCESO').count()
    en_camino = Vehiculo.objects.filter(estado='EN_CAMINO').count()
    entregados = Vehiculo.objects.filter(estado='ENTREGADO').count()

    return render(request, 'logistica/dashboard.html', {
        'vehiculos': vehiculos,
        'form': VehiculoForm(),
        'form_buque': BuqueForm(),
        'form_cliente': ClienteForm(),
        'form_camion': CamionCiguenaForm(),
        'total': total,
        'encontrados': encontrados,
        'en_proceso': en_proceso,
        'en_camino': en_camino,
        'entregados': entregados,
        'q': q,
        'filtro_estado': filtro_estado,
        'estados': Vehiculo.ESTADOS,
        'buques': Buque.objects.all().order_by('-fecha_atraque'),
        'clientes': Cliente.objects.all().order_by('nombre_completo'),
        'camiones': CamionCiguena.objects.all().order_by('patente'),
        'es_operador': es_operador(request.user),
    })


# Guardar nuevo buque desde el modal
@solo_operadores
def registrar_buque(request):
    if request.method == 'POST':
        form = BuqueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Buque registrado exitosamente.")
        else:
            messages.error(request, "Error al registrar buque.")
    return redirect('dashboard')


# Guardar nuevo cliente desde el modal
@solo_operadores
def registrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente registrado exitosamente.")
        else:
            messages.error(request, "Error al registrar cliente.")
    return redirect('dashboard')


# Guardar nuevo camión cigüeña desde el modal
@solo_operadores
def registrar_camion(request):
    if request.method == 'POST':
        form = CamionCiguenaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Camión cigüeña registrado exitosamente.")
        else:
            messages.error(request, "Error al registrar camión.")
    return redirect('dashboard')


# Guardar nuevo vehículo desde el modal
@solo_operadores
def registrar_vehiculo(request):
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            vehiculo = form.save()
            HistorialEstado.objects.create(
                vehiculo=vehiculo,
                estado_anterior=None,
                estado_nuevo=vehiculo.estado,
                ubicacion_patio=vehiculo.ubicacion_patio,
                usuario=request.user,
            )
            messages.success(request, "Vehículo ingresado al manifiesto.")
        else:
            messages.error(request, "Error al registrar vehículo. Verifique los campos.")
    return redirect('dashboard')


# Actualización rápida de estado y patio desde la tabla
@solo_operadores
def actualizar_estado_vehiculo(request, pk):
    if request.method == 'POST':
        vehiculo = get_object_or_404(Vehiculo, pk=pk)
        estado_anterior = vehiculo.estado
        ubicacion_anterior = vehiculo.ubicacion_patio or ''
        nuevo_estado = request.POST.get('nuevo_estado') or vehiculo.estado
        nueva_ubicacion = request.POST.get('ubicacion_patio')

        vehiculo.estado = nuevo_estado
        if nueva_ubicacion is not None:
            vehiculo.ubicacion_patio = nueva_ubicacion.strip()

        cambio_estado = vehiculo.estado != estado_anterior
        cambio_ubicacion = (vehiculo.ubicacion_patio or '') != ubicacion_anterior
        vehiculo.save()

        if cambio_estado or cambio_ubicacion:
            HistorialEstado.objects.create(
                vehiculo=vehiculo,
                estado_anterior=estado_anterior,
                estado_nuevo=vehiculo.estado,
                ubicacion_patio=vehiculo.ubicacion_patio,
                usuario=request.user,
            )
        messages.success(request, f"Actualizado chasis {vehiculo.chasis}.")
    return redirect('dashboard')


# --------------------------------------------------------------------------
# Eliminar registros (CRUD Unidad 2)
# --------------------------------------------------------------------------

@solo_operadores
def eliminar_vehiculo(request, pk):
    if request.method == 'POST':
        vehiculo = get_object_or_404(Vehiculo, pk=pk)
        chasis = vehiculo.chasis
        vehiculo.delete()
        messages.success(request, f"Vehículo con chasis {chasis} eliminado.")
    return redirect('dashboard')


@solo_operadores
def eliminar_buque(request, pk):
    if request.method == 'POST':
        buque = get_object_or_404(Buque, pk=pk)
        nombre = buque.nombre
        cantidad_vehiculos = buque.vehiculos.count()
        buque.delete()
        if cantidad_vehiculos:
            messages.warning(
                request,
                f"Buque '{nombre}' eliminado junto con {cantidad_vehiculos} vehículo(s) asociado(s)."
            )
        else:
            messages.success(request, f"Buque '{nombre}' eliminado.")
    return redirect('dashboard')


@solo_operadores
def eliminar_cliente(request, pk):
    if request.method == 'POST':
        cliente = get_object_or_404(Cliente, pk=pk)
        nombre = cliente.nombre_completo
        cantidad_vehiculos = cliente.vehiculos.count()
        cliente.delete()
        if cantidad_vehiculos:
            messages.warning(
                request,
                f"Cliente '{nombre}' eliminado junto con {cantidad_vehiculos} vehículo(s) asociado(s)."
            )
        else:
            messages.success(request, f"Cliente '{nombre}' eliminado.")
    return redirect('dashboard')


@solo_operadores
def eliminar_camion(request, pk):
    if request.method == 'POST':
        camion = get_object_or_404(CamionCiguena, pk=pk)
        patente = camion.patente
        camion.delete()
        messages.success(request, f"Camión cigüeña '{patente}' eliminado.")
    return redirect('dashboard')