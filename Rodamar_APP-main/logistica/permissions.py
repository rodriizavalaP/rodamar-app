from rest_framework.permissions import BasePermission


class EsOperadorOSoloLectura(BasePermission):
    """
    Regla de seguridad de la API:

    La API interna contiene datos personales (RUT, teléfonos, choferes), por
    lo que SOLO la pueden usar superusuarios y miembros del grupo
    'Operadores', tanto para leer como para escribir.

    Las cuentas de registro público ('Clientes') reciben 403. La consulta
    abierta para terceros existe aparte, en /api/rastreo/<chasis>/, y solo
    devuelve datos no sensibles.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or user.groups.filter(name='Operadores').exists()
