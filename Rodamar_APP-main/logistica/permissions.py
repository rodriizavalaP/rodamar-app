from rest_framework.permissions import BasePermission, SAFE_METHODS


class EsOperadorOSoloLectura(BasePermission):
    """
    Regla de seguridad de la API (Unidad 3):

    - Lectura (GET / HEAD / OPTIONS): cualquier usuario autenticado
      (por sesión o por JWT) puede consultar.
    - Escritura (POST / PUT / PATCH / DELETE): solo superusuarios o
      usuarios que pertenezcan al grupo 'Operadores'. Las cuentas creadas
      públicamente pertenecen al grupo 'Clientes' y quedan en solo lectura.

    Así se replica en la API la misma jerarquía de roles que ya existe
    en el panel HTML (ADMIN / OPERADOR / CLIENTE / INVITADO).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.is_superuser or request.user.groups.filter(name='Operadores').exists()
