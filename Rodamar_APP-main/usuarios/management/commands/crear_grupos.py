from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Crea los grupos de roles de RODAMAR: Clientes y Operadores."

    def handle(self, *args, **options):
        for nombre in ("Clientes", "Operadores"):
            grupo, creado = Group.objects.get_or_create(name=nombre)
            if creado:
                self.stdout.write(self.style.SUCCESS(f"Grupo '{nombre}' creado."))
            else:
                self.stdout.write(f"Grupo '{nombre}' ya existía.")
