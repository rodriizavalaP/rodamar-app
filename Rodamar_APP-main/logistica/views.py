from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from .models import Vehiculo, Buque, Cliente, CamionCiguena, HistorialEstado, FotoVehiculo, Contenedor
from .forms import VehiculoForm, BuqueForm, ClienteForm, CamionCiguenaForm, ContenedorForm


def es_operador(user):
    """
    Solo superusuarios o miembros del grupo 'Operadores' pueden ver el
    panel y escribir datos. Las cuentas de registro publico pertenecen al
    grupo 'Clientes' y no tienen acceso al panel (ver usuarios/views.py).
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

    puede_ver_clientes = es_operador(request.user)

    if query:
        # 1. Busqueda publica: solo por numero de chasis (VIN) exacto
        vehiculo = Vehiculo.objects.select_related('buque', 'cliente', 'camion_ciguena').filter(chasis__iexact=query).first()

        if vehiculo:
            historial = vehiculo.historial.all()
        elif puede_ver_clientes:
            # 2. Solo operadores: buscar por RUT o nombre de cliente / flota
            clientes = Cliente.objects.filter(
                Q(rut_o_id__iexact=query) | Q(nombre_completo__icontains=query)
            )
            if clientes.exists():
                cliente_encontrado = clientes.first()
                vehiculos_empresa = Vehiculo.objects.filter(cliente=cliente_encontrado).select_related('buque', 'camion_ciguena')
            else:
                coincidencias = Vehiculo.objects.filter(chasis__icontains=query).select_related('buque', 'cliente', 'camion_ciguena')
                if coincidencias.exists():
                    vehiculos_empresa = coincidencias

        if not vehiculo and not vehiculos_empresa:
            mensaje_error = f"No se encontraron vehiculos con el chasis '{query}'."

    return render(request, 'logistica/rastreo.html', {
        'vehiculo': vehiculo,
        'historial': historial,
        'vehiculos_empresa': vehiculos_empresa,
        'cliente_encontrado': cliente_encontrado,
        'termino': query,
        'query': query,
        'mensaje_error': mensaje_error,
        'puede_ver_clientes': puede_ver_clientes,
    })


# Vista privada: Panel operativo para el operador
@login_required
def dashboard_operaciones(request):
    # Los Clientes no ven datos de otros clientes: el panel es del personal.
    if not es_operador(request.user):
        messages.warning(request, "El panel operativo es solo para operadores. Puedes consultar tu vehiculo por chasis en Rastreo.")
        return redirect('rastreo')

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
    no_encontrados = Vehiculo.objects.filter(estado='NO_ENCONTRADO').count()
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
        'no_encontrados': no_encontrados,
        'encontrados': encontrados,
        'en_proceso': en_proceso,
        'en_camino': en_camino,
        'entregados': entregados,
        'q': q,
        'filtro_estado': filtro_estado,
        'estados': Vehiculo.ESTADOS,
        'ciguenas': CamionCiguena.objects.all(),
        'buques': Buque.objects.all().order_by('-fecha_atraque'),
        'clientes': Cliente.objects.all().order_by('nombre_completo'),
        'camiones': CamionCiguena.objects.all().order_by('patente'),
        'es_operador': es_operador(request.user),
    })



# --------------------------------------------------------------------------
# Utilidades del CRUD web
# --------------------------------------------------------------------------

def _errores_de(form):
    """Convierte los errores de un formulario en un texto legible."""
    partes = []
    for campo, errores in form.errors.items():
        etiqueta = (form.fields[campo].label or campo) if campo in form.fields else 'Formulario'
        partes.append(f"{etiqueta}: {' '.join(errores)}")
    return ' | '.join(partes)


def _volver(request, defecto):
    """Destino tras guardar. Solo se aceptan nombres de ruta conocidos."""
    destino = request.POST.get('volver', defecto)
    return destino if destino in ('dashboard', 'gestion') else defecto


# Guardar nuevo buque desde el modal
@solo_operadores
def registrar_buque(request):
    if request.method == 'POST':
        form = BuqueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Buque registrado exitosamente.")
        else:
            messages.error(request, f"No se pudo registrar el buque. {_errores_de(form)}")
    return redirect(_volver(request, 'gestion'))


# Guardar nuevo cliente desde el modal
@solo_operadores
def registrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente registrado exitosamente.")
        else:
            messages.error(request, f"No se pudo registrar el cliente. {_errores_de(form)}")
    return redirect(_volver(request, 'gestion'))


# Guardar nuevo camión cigüeña desde el modal
@solo_operadores
def registrar_camion(request):
    if request.method == 'POST':
        form = CamionCiguenaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Camión cigüeña registrado exitosamente.")
        else:
            messages.error(request, f"No se pudo registrar el camión. {_errores_de(form)}")
    return redirect(_volver(request, 'gestion'))


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
            messages.error(request, f"No se pudo registrar el vehículo. {_errores_de(form)}")
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

        # En traslado: sale por sus propios medios o cargado en una cigüeña
        traslado = request.POST.get('traslado', '')
        camion_historial = vehiculo.camion_ciguena
        nota = ''
        if nuevo_estado == 'EN_CAMINO' and traslado:
            if traslado == 'propio':
                vehiculo.camion_ciguena = None
                camion_historial = None
                nota = 'Sale por sus propios medios'
            elif traslado.isdigit():
                camion = CamionCiguena.objects.filter(pk=int(traslado)).first()
                if camion is None:
                    messages.error(request, "La cigüeña elegida no existe.")
                    return redirect('dashboard')
                if vehiculo.camion_ciguena_id != camion.pk and camion.cupos_libres < 1:
                    messages.error(request, f"La cigüeña {camion.patente} no tiene cupos libres.")
                    return redirect('dashboard')
                vehiculo.camion_ciguena = camion
                camion_historial = camion
                nota = f'Cargado en la cigüeña {camion.patente}'

        cambio_estado = vehiculo.estado != estado_anterior
        cambio_ubicacion = (vehiculo.ubicacion_patio or '') != ubicacion_anterior
        vehiculo.save()

        if cambio_estado or cambio_ubicacion or nota:
            HistorialEstado.objects.create(
                vehiculo=vehiculo,
                estado_anterior=estado_anterior,
                estado_nuevo=vehiculo.estado,
                ubicacion_patio=vehiculo.ubicacion_patio,
                usuario=request.user,
                camion_ciguena=camion_historial,
                nota=nota,
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
    return redirect(_volver(request, 'gestion'))


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
    return redirect(_volver(request, 'gestion'))


@solo_operadores
def eliminar_camion(request, pk):
    if request.method == 'POST':
        camion = get_object_or_404(CamionCiguena, pk=pk)
        patente = camion.patente
        camion.delete()
        messages.success(request, f"Camión cigüeña '{patente}' eliminado.")
    return redirect(_volver(request, 'gestion'))


# --------------------------------------------------------------------------
# Gestión de catálogos (Buques, Clientes, Camiones) y edición (Update del CRUD)
# --------------------------------------------------------------------------

@solo_operadores
def gestion_catalogos(request):
    return render(request, 'logistica/gestion.html', {
        'buques': Buque.objects.all().order_by('-fecha_atraque'),
        'clientes': Cliente.objects.all().order_by('nombre_completo'),
        'camiones': CamionCiguena.objects.all().order_by('patente'),
        'form_buque': BuqueForm(),
        'form_cliente': ClienteForm(),
        'form_camion': CamionCiguenaForm(),
        'contenedores': Contenedor.objects.all().annotate(total=Count('vehiculos')),
        'form_contenedor': ContenedorForm(),
    })


def _editar(request, modelo, form_class, pk, titulo, destino):
    """Vista genérica de edición: GET muestra el formulario, POST valida y guarda."""
    objeto = get_object_or_404(modelo, pk=pk)
    if request.method == 'POST':
        form = form_class(request.POST, instance=objeto)
        if form.is_valid():
            form.save()
            messages.success(request, f"{titulo} actualizado correctamente.")
            return redirect(destino)
        messages.error(request, "Revisa los campos marcados.")
    else:
        form = form_class(instance=objeto)
    return render(request, 'logistica/editar.html', {
        'form': form, 'titulo': titulo, 'objeto': objeto, 'destino': destino,
    })


@solo_operadores
def editar_buque(request, pk):
    return _editar(request, Buque, BuqueForm, pk, 'Buque', 'gestion')


@solo_operadores
def editar_cliente(request, pk):
    return _editar(request, Cliente, ClienteForm, pk, 'Cliente', 'gestion')


@solo_operadores
def editar_camion(request, pk):
    return _editar(request, CamionCiguena, CamionCiguenaForm, pk, 'Camión cigüeña', 'gestion')


@solo_operadores
def editar_vehiculo(request, pk):
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    # Se guarda lo anterior ANTES de validar, porque el form modifica la instancia.
    estado_anterior = vehiculo.estado
    ubicacion_anterior = vehiculo.ubicacion_patio or ''

    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            vehiculo = form.save()
            if vehiculo.estado != estado_anterior or (vehiculo.ubicacion_patio or '') != ubicacion_anterior:
                HistorialEstado.objects.create(
                    vehiculo=vehiculo,
                    estado_anterior=estado_anterior,
                    estado_nuevo=vehiculo.estado,
                    ubicacion_patio=vehiculo.ubicacion_patio,
                    usuario=request.user,
                )
            messages.success(request, f"Vehículo {vehiculo.chasis} actualizado correctamente.")
            return redirect('dashboard')
        messages.error(request, "Revisa los campos marcados.")
    else:
        form = VehiculoForm(instance=vehiculo)
    return render(request, 'logistica/editar.html', {
        'form': form, 'titulo': 'Vehículo', 'objeto': vehiculo, 'destino': 'dashboard',
    })


# --------------------------------------------------------------------------
# Cigüeña: varios vehículos en un mismo viaje y su seguimiento
# --------------------------------------------------------------------------

@solo_operadores
def detalle_camion(request, pk):
    camion = get_object_or_404(CamionCiguena, pk=pk)
    cargados = camion.vehiculos_cargados.select_related('buque', 'cliente').order_by('chasis')
    disponibles = Vehiculo.objects.filter(camion_ciguena__isnull=True).exclude(
        estado='ENTREGADO').select_related('buque', 'cliente').order_by('chasis')
    movimientos = camion.movimientos.select_related('vehiculo', 'usuario')[:30]
    return render(request, 'logistica/detalle_camion.html', {
        'camion': camion,
        'cargados': cargados,
        'disponibles': disponibles,
        'movimientos': movimientos,
    })


@solo_operadores
def asignar_vehiculos(request, pk):
    """Asigna varios vehículos seleccionados a una cigüeña, respetando su capacidad."""
    camion = get_object_or_404(CamionCiguena, pk=pk)
    if request.method == 'POST':
        ids = request.POST.getlist('vehiculos')
        vehiculos = list(Vehiculo.objects.filter(pk__in=ids, camion_ciguena__isnull=True))

        if not vehiculos:
            messages.error(request, "Selecciona al menos un vehículo disponible.")
        elif len(vehiculos) > camion.cupos_libres:
            messages.error(
                request,
                f"La cigüeña {camion.patente} solo tiene {camion.cupos_libres} cupo(s) libre(s) "
                f"y seleccionaste {len(vehiculos)}."
            )
        else:
            en_traslado = request.POST.get('marcar_en_camino') == 'on'
            for v in vehiculos:
                estado_anterior = v.estado
                v.camion_ciguena = camion
                if en_traslado:
                    v.estado = 'EN_CAMINO'
                v.save()
                HistorialEstado.objects.create(
                    vehiculo=v,
                    estado_anterior=estado_anterior,
                    estado_nuevo=v.estado,
                    ubicacion_patio=v.ubicacion_patio,
                    usuario=request.user,
                    camion_ciguena=camion,
                    nota=f"Asignado a la cigüeña {camion.patente}",
                )
            messages.success(
                request,
                f"{len(vehiculos)} vehículo(s) asignado(s) a la cigüeña {camion.patente}."
            )
    return redirect('detalle_camion', pk=camion.pk)


@solo_operadores
def asignar_ciguena_vehiculo(request, pk):
    """Asigna (o quita) la cigüeña de un solo vehículo desde el panel."""
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    if request.method == 'POST':
        eleccion = request.POST.get('ciguena', '')
        anterior = vehiculo.camion_ciguena
        if eleccion == '':
            if anterior is None:
                return redirect('dashboard')
            vehiculo.camion_ciguena = None
            vehiculo.save()
            HistorialEstado.objects.create(
                vehiculo=vehiculo, estado_anterior=vehiculo.estado, estado_nuevo=vehiculo.estado,
                ubicacion_patio=vehiculo.ubicacion_patio, usuario=request.user,
                nota=f"Retirado de la cigüeña {anterior.patente}",
            )
            messages.success(request, f"{vehiculo.chasis} ya no va en cigüeña.")
        else:
            camion = get_object_or_404(CamionCiguena, pk=eleccion)
            if anterior_id_distinto(vehiculo, camion) and camion.cupos_libres < 1:
                messages.error(request, f"La cigüeña {camion.patente} no tiene cupos libres.")
            else:
                vehiculo.camion_ciguena = camion
                vehiculo.save()
                HistorialEstado.objects.create(
                    vehiculo=vehiculo, estado_anterior=vehiculo.estado, estado_nuevo=vehiculo.estado,
                    ubicacion_patio=vehiculo.ubicacion_patio, usuario=request.user,
                    camion_ciguena=camion, nota=f"Asignado a la cigüeña {camion.patente}",
                )
                messages.success(request, f"{vehiculo.chasis} asignado a la cigüeña {camion.patente}.")
    return redirect('dashboard')


def anterior_id_distinto(vehiculo, camion):
    return vehiculo.camion_ciguena_id != camion.pk


@solo_operadores
def quitar_vehiculo_de_camion(request, pk, vehiculo_pk):
    camion = get_object_or_404(CamionCiguena, pk=pk)
    if request.method == 'POST':
        vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_pk, camion_ciguena=camion)
        vehiculo.camion_ciguena = None
        vehiculo.save()
        HistorialEstado.objects.create(
            vehiculo=vehiculo,
            estado_anterior=vehiculo.estado,
            estado_nuevo=vehiculo.estado,
            ubicacion_patio=vehiculo.ubicacion_patio,
            usuario=request.user,
            camion_ciguena=camion,
            nota=f"Retirado de la cigüeña {camion.patente}",
        )
        messages.success(request, f"{vehiculo.chasis} fue retirado de la cigüeña {camion.patente}.")
    return redirect('detalle_camion', pk=camion.pk)


# --------------------------------------------------------------------------
# Detalle del vehículo y fotos del chequeo
# --------------------------------------------------------------------------

MAX_FOTO_BYTES = 2 * 1024 * 1024  # 2 MB (Vercel limita el tamaño de cada petición)


def _tipo_imagen(datos):
    """Detecta el formato real mirando los primeros bytes (no confía en el nombre)."""
    if datos[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if datos[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if datos[:4] == b'RIFF' and datos[8:12] == b'WEBP':
        return 'image/webp'
    return None


@solo_operadores
def detalle_vehiculo(request, pk):
    vehiculo = get_object_or_404(
        Vehiculo.objects.select_related('buque', 'cliente', 'camion_ciguena'), pk=pk)
    # defer('imagen') evita traer los bytes de las fotos solo para listarlas
    fotos = vehiculo.fotos.defer('imagen').select_related('usuario')
    return render(request, 'logistica/detalle_vehiculo.html', {
        'vehiculo': vehiculo,
        'fotos': fotos,
        'historial': vehiculo.historial.select_related('usuario', 'camion_ciguena'),
        'tipos_foto': FotoVehiculo.TIPOS,
    })


@solo_operadores
def subir_foto(request, pk):
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    if request.method == 'POST':
        archivos = request.FILES.getlist('imagenes')
        tipo = request.POST.get('tipo', 'LLEGADA')
        descripcion = request.POST.get('descripcion', '').strip()[:160]

        if tipo not in dict(FotoVehiculo.TIPOS):
            tipo = 'LLEGADA'
        if not archivos:
            messages.error(request, "Elige al menos una foto.")
            return redirect('detalle_vehiculo', pk=vehiculo.pk)

        guardadas, rechazadas = 0, []
        for archivo in archivos:
            if archivo.size > MAX_FOTO_BYTES:
                rechazadas.append(f"{archivo.name} (supera 2 MB)")
                continue
            datos = archivo.read()
            content_type = _tipo_imagen(datos)
            if not content_type:
                rechazadas.append(f"{archivo.name} (no es JPG, PNG ni WEBP)")
                continue
            FotoVehiculo.objects.create(
                vehiculo=vehiculo, tipo=tipo, descripcion=descripcion,
                imagen=datos, content_type=content_type, usuario=request.user,
            )
            guardadas += 1

        if guardadas:
            messages.success(request, f"{guardadas} foto(s) guardada(s).")
        if rechazadas:
            messages.error(request, "No se guardaron: " + ", ".join(rechazadas))
    return redirect('detalle_vehiculo', pk=vehiculo.pk)


@solo_operadores
def ver_foto(request, pk):
    """Entrega la imagen guardada en la base de datos (solo para operadores)."""
    foto = get_object_or_404(FotoVehiculo, pk=pk)
    respuesta = HttpResponse(bytes(foto.imagen), content_type=foto.content_type)
    respuesta['Cache-Control'] = 'private, max-age=3600'
    respuesta['X-Content-Type-Options'] = 'nosniff'
    return respuesta


@solo_operadores
def eliminar_foto(request, pk):
    foto = get_object_or_404(FotoVehiculo.objects.defer('imagen'), pk=pk)
    vehiculo_pk = foto.vehiculo_id
    if request.method == 'POST':
        foto.delete()
        messages.success(request, "Foto eliminada.")
    return redirect('detalle_vehiculo', pk=vehiculo_pk)


# --------------------------------------------------------------------------
# Contenedores: vehículos que llegan dentro de un contenedor
# --------------------------------------------------------------------------

@solo_operadores
def registrar_contenedor(request):
    if request.method == 'POST':
        form = ContenedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contenedor registrado exitosamente.")
        else:
            messages.error(request, f"No se pudo registrar el contenedor. {_errores_de(form)}")
    return redirect(_volver(request, 'gestion'))


@solo_operadores
def editar_contenedor(request, pk):
    return _editar(request, Contenedor, ContenedorForm, pk, 'Contenedor', 'gestion')


@solo_operadores
def eliminar_contenedor(request, pk):
    if request.method == 'POST':
        contenedor = get_object_or_404(Contenedor, pk=pk)
        numero = contenedor.numero
        cantidad = contenedor.vehiculos.count()
        contenedor.delete()  # los vehículos NO se borran: solo quedan sin contenedor
        if cantidad:
            messages.warning(request, f"Contenedor {numero} eliminado. {cantidad} vehículo(s) quedaron sin contenedor.")
        else:
            messages.success(request, f"Contenedor {numero} eliminado.")
    return redirect('gestion')


@solo_operadores
def detalle_contenedor(request, pk):
    contenedor = get_object_or_404(Contenedor, pk=pk)
    return render(request, 'logistica/detalle_contenedor.html', {
        'contenedor': contenedor,
        'vehiculos': contenedor.vehiculos.select_related('buque', 'cliente').order_by('chasis'),
        'disponibles': Vehiculo.objects.filter(contenedor__isnull=True).select_related(
            'buque', 'cliente').order_by('chasis'),
    })


@solo_operadores
def agregar_vehiculos_a_contenedor(request, pk):
    """Anota que los vehículos seleccionados venían dentro de este contenedor."""
    contenedor = get_object_or_404(Contenedor, pk=pk)
    if request.method == 'POST':
        vehiculos = list(Vehiculo.objects.filter(
            pk__in=request.POST.getlist('vehiculos'), contenedor__isnull=True))
        if not vehiculos:
            messages.error(request, "Selecciona al menos un vehículo.")
        else:
            for v in vehiculos:
                v.contenedor = contenedor
                v.save()
                HistorialEstado.objects.create(
                    vehiculo=v,
                    estado_anterior=v.estado,
                    estado_nuevo=v.estado,
                    ubicacion_patio=v.ubicacion_patio,
                    usuario=request.user,
                    nota=f"Descargado del contenedor {contenedor.numero}",
                )
            messages.success(request, f"{len(vehiculos)} vehículo(s) anotado(s) en el contenedor {contenedor.numero}.")
    return redirect('detalle_contenedor', pk=contenedor.pk)


@solo_operadores
def quitar_vehiculo_de_contenedor(request, pk, vehiculo_pk):
    contenedor = get_object_or_404(Contenedor, pk=pk)
    if request.method == 'POST':
        vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_pk, contenedor=contenedor)
        vehiculo.contenedor = None
        vehiculo.save()
        messages.success(request, f"{vehiculo.chasis} ya no figura en el contenedor {contenedor.numero}.")
    return redirect('detalle_contenedor', pk=contenedor.pk)
