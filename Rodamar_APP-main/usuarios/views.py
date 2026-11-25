from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import RegistroForm

# El registro público crea cuentas con rol CLIENTE. Los roles OPERADOR y
# ADMIN se asignan de forma controlada desde el panel de administración.
GRUPO_CLIENTES = 'Clientes'


def registro_view(request):
    """
    Registro público para el rol CLIENTE. El usuario creado nunca recibe
    is_staff/is_superuser ni permisos de operador desde este formulario.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()  # is_staff/is_superuser quedan en False por defecto

            grupo_clientes, _ = Group.objects.get_or_create(name=GRUPO_CLIENTES)
            usuario.groups.add(grupo_clientes)

            login(request, usuario)
            messages.success(request, f"¡Bienvenido, {usuario.username}! Tu cuenta fue creada.")
            return redirect('rastreo')
        else:
            messages.error(request, "Revisa los datos ingresados.")
    else:
        form = RegistroForm()

    return render(request, 'registro.html', {'form': form})
