# Mejoras implementadas en RODAMAR

## 1. Roles y seguridad
- El registro público crea usuarios con el grupo `Clientes`.
- El grupo `Operadores` queda reservado para personal autorizado.
- Los roles de operador/administrador se asignan desde Django Admin.
- Se corrigió la ruta del template de registro.

## 2. Trazabilidad ampliada
El historial ahora se registra cuando cambia:
- el estado del vehículo;
- la ubicación dentro del patio;
- o ambos.

Esto permite justificar la trazabilidad operativa de RODAMAR incluso cuando un vehículo se mueve de posición sin cambiar su estado general.

La misma lógica se aplica al panel web y a las actualizaciones realizadas mediante la API REST.

## 3. Datos de demostración
Se agregó el comando:

```bash
python manage.py crear_grupos
python manage.py cargar_datos_demo
```

El segundo comando crea datos demostrativos de buques, clientes, camiones cigüeña y vehículos, además de su historial inicial.

Usuario operador demo:

```text
usuario: operador_demo
clave: RodamarDemo2026!
```

> Esta cuenta es solamente para demostración/desarrollo. En producción debe utilizarse una contraseña segura y gestionada fuera del código fuente.

## 4. Prueba agregada
Se incorporó una prueba para comprobar que un cambio exclusivamente de ubicación también genera un registro en `HistorialEstado`.
