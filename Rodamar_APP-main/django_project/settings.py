from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Si no esta instalado mysqlclient (por ejemplo en Vercel), se usa PyMySQL
# como reemplazo compatible.
try:
    import MySQLdb  # noqa: F401
except ImportError:
    import pymysql
    pymysql.version_info = (2, 2, 1, 'final', 0)
    pymysql.install_as_MySQLdb()

# Carga las variables definidas en el archivo .env (no se sube a git)
load_dotenv(BASE_DIR / '.env')

# La SECRET_KEY se lee desde el entorno. Si no existe (por ejemplo, alguien
# clonó el repo y no creó su .env), Django avisa altiro en vez de arrancar
# con una clave vacía o insegura.
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError(
        "Falta SECRET_KEY. Crea un archivo .env en la raíz del proyecto "
        "(mira .env.example) con SECRET_KEY=tu_clave_generada."
    )

# DEBUG también sale del entorno, por defecto en False (modo producción)
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []

# Aplicaciones del proyecto
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros
    'rest_framework',
    # Tus Apps
    'pages',
    'logistica',
    'usuarios',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'django_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_project.wsgi.application'

# Base de datos MySQL. Las credenciales se leen del archivo .env (ver
# .env.example); para cambiarlas basta editar ese archivo, no el código.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'rodamar_db'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Para MySQL en la nube (TiDB, Aiven, etc.) que exigen conexion cifrada:
# poner DB_SSL=True en las variables de entorno.
if os.getenv('DB_SSL', 'False') == 'True':
    import certifi
    DATABASES['default']['OPTIONS']['ssl'] = {'ca': certifi.where()}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configuración Regional
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Sirve los estaticos directamente desde la app (necesario en Vercel)
WHITENOISE_USE_FINDERS = True

# Dominios permitidos para formularios con CSRF (ej: https://mi-app.vercel.app)
CSRF_TRUSTED_ORIGINS = [o for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Rutas de autenticación
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/logistica/panel/'
LOGOUT_REDIRECT_URL = '/'

# --------------------------------------------------------------------------
# Django REST Framework (Unidad 3: API, serializers, CRUD REST y seguridad)
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Autenticación: JWT para clientes externos (apps móviles, terceros) y
    # Sesión para poder probar la API desde el navegador estando logueado.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    # Por defecto nada es público: cada vista/viewset decide su excepción
    # (por ejemplo, el rastreo público usa AllowAny explícitamente).
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    # Seguridad adicional: limitar peticiones para evitar abuso/DoS básico.
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'user': '120/minute',
        'anon': '20/minute',
    },
}

# Configuración de tokens JWT (djangorestframework-simplejwt)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Nombre del grupo que puede escribir en el panel/API (ver usuarios/views.py)
GRUPO_OPERADORES = 'Operadores'