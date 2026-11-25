# RODAMAR – Logística y trazabilidad de vehículos (Django + MySQL)

Sistema web para el muellaje de vehículos en puerto: registro de buques, clientes,
camiones cigüeña y vehículos, con trazabilidad de estado y ubicación en patio.

- **Problemática:** el seguimiento de vehículos descargados se hace de forma manual y dispersa.
- **Objetivo:** centralizar el registro y la trazabilidad de cada vehículo (chasis/VIN).
- **Roles:** *Visitante* (rastreo público por chasis), *Cliente* (cuenta de registro público, sin acceso al panel), *Operador* (panel y CRUD completo) y *Administrador* (superusuario, Django Admin).

## Requisitos
- Python 3.11 o superior
- MySQL 8.x (o MariaDB compatible) en ejecución
- Django 5.2.17 (se instala desde `requirements.txt`)

## Instalación

```bash
# 1. Entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 2. Dependencias
pip install -r requirements.txt
```

> `mysqlclient` en Windows suele instalarse sin problemas desde su paquete precompilado.
> En Linux puede requerir: `sudo apt install pkg-config default-libmysqlclient-dev build-essential`.

## Configuración de MySQL

1. Crea la base de datos en MySQL:

```sql
CREATE DATABASE rodamar_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Copia el archivo de ejemplo y edita tus credenciales:

```bash
copy .env.example .env         # Windows
# cp .env.example .env         # Linux / macOS
```

3. **Las credenciales de MySQL se modifican únicamente en el archivo `.env`:**

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta de Django | genera una con el comando indicado en `.env.example` |
| `DEBUG` | Modo desarrollo | `True` |
| `DB_NAME` | Nombre de la base | `rodamar_db` |
| `DB_USER` | Usuario MySQL | `root` |
| `DB_PASSWORD` | Contraseña MySQL | tu contraseña |
| `DB_HOST` | Servidor | `127.0.0.1` |
| `DB_PORT` | Puerto | `3306` |

La conexión está definida en `django_project/settings.py` (sección `DATABASES`) y lee esas variables.

## Migraciones y datos iniciales

```bash
python manage.py migrate
python manage.py crear_grupos          # crea los grupos Operadores y Clientes
python manage.py cargar_datos_demo     # datos de ejemplo + usuario de prueba
python manage.py runserver
```

Abre http://127.0.0.1:8000/

## Usuario de prueba (solo para evaluación)

| Rol | Usuario | Contraseña |
|---|---|---|
| Operador (CRUD completo) | `operador_demo` | `RodamarDemo2026!` |

Es una cuenta creada solo para evaluar el sistema; no corresponde a credenciales reales.
Para entrar a Django Admin (`/admin/`) crea un administrador con:

```bash
python manage.py createsuperuser
```

Para probar el rol *Cliente*, usa **Registro** en el sitio: esas cuentas no pueden entrar al panel.

## Funcionalidades (CRUD desde el sitio, sin Django Admin)

| Entidad | Crear | Consultar | Modificar | Eliminar | Dónde |
|---|---|---|---|---|---|
| Vehículo | ✔ | ✔ | ✔ (datos completos y estado rápido) | ✔ | Panel `/logistica/panel/` |
| Buque | ✔ | ✔ | ✔ | ✔ | Gestión `/logistica/gestion/` |
| Cliente | ✔ | ✔ | ✔ | ✔ | Gestión `/logistica/gestion/` |
| Camión cigüeña | ✔ | ✔ | ✔ | ✔ | Gestión `/logistica/gestion/` |

- Los formularios validan en el servidor (campos obligatorios, chasis y RUT únicos, formato de fecha y correo) y muestran mensajes de éxito o error.
- Eliminar pide confirmación.
- Cada cambio de estado o ubicación de un vehículo queda en `HistorialEstado` (quién, cuándo y qué cambió).
- Login/logout con sesiones de Django; protección CSRF en todos los formularios.
- Rastreo público (`/logistica/rastreo/`): solo por chasis exacto y sin datos personales del cliente.

## Cigüeña con varios vehículos y fotos de chequeo
- **Cigüeña:** cada camión tiene una capacidad. En *Clientes y catálogos → Camiones → Carga* se seleccionan varios vehículos que viajan juntos; el sistema respeta los cupos, puede marcarlos «En traslado» y deja cada asignación o retiro en el historial (con usuario y fecha).
- **Fotos:** en el panel, el botón de la cámara de cada vehículo abre su ficha. Ahí se suben fotos (JPG, PNG o WEBP, máx. 2 MB c/u) con tipo (llegada, chequeo, daño, entrega) y observación; al hacer clic en una foto se abre ampliada. Las fotos solo las ven los operadores.
- **Contenedores:** si los vehículos llegan dentro de un contenedor, se registra su número (formato ISO: 4 letras y 7 números, ej. `MSKU1234567`), sello y fecha de apertura en *Clientes y catálogos → Contenedores*. Cada vehículo puede indicar su contenedor (al crearlo/editarlo, o desde la página del contenedor) y se ve en el panel y en su ficha. Eliminar un contenedor no borra los vehículos.
- Las imágenes se guardan en la base de datos, por lo que funcionan igual en local y en la nube.
- Tras actualizar el código, ejecutar `python manage.py migrate` (migraciones `0003` y `0004`).

## Seguridad básica
- `SECRET_KEY` y credenciales de MySQL salen de `.env` (que no se sube a Git, ver `.gitignore`).
- Acceso restringido por rol: el panel, la gestión, la edición y la API interna son solo para Operadores/Administradores.
- La API REST y JWT (`/api/`) son un extra de la Unidad 3; no son requisito de esta evaluación.

## Pruebas

```bash
python manage.py test
```

(Usa una base de prueba temporal; el usuario de MySQL debe poder crear bases de datos.)

## Estructura

```
django_project/   configuración (settings, urls)
pages/            página de inicio
logistica/        modelos, vistas, formularios, CRUD, API
usuarios/         registro de usuarios y comandos de datos demo
templates/        plantillas HTML (base, home, registro, login, logistica/*)
static/           imágenes y recursos estáticos
```
