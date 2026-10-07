from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize django-environ with schemas and sensible defaults
env = environ.Env(
    DEBUG=(bool, False),
    PRODUCTION=(bool, False),
    SECRET_KEY=(str, 'django-insecure-n1th0c$%az@*zml=2zhke)h(azu9jw_is(y2@rb0-=-+4+n@2c'),
    ALLOWED_HOSTS=(list, ['127.0.0.1', 'localhost', 'testserver']),
    CSRF_TRUSTED_ORIGINS=(list, []),
    LANGUAGE_CODE=(str, 'es-es'),
    TIME_ZONE=(str, 'UTC'),
    # Active Directory / LDAP
    LDAP_ENABLED=(bool, False),
    LDAP_SERVER_URI=(str, 'ldap://127.0.0.1:389'),
    LDAP_PORT=(int, 389),
    LDAP_USE_SSL=(bool, False),
    LDAP_CONNECT_TIMEOUT=(int, 5),
    LDAP_DOMAIN=(str, ''),
    LDAP_BIND_DN=(str, ''),
    LDAP_BIND_PASSWORD=(str, ''),
    LDAP_SEARCH_BASE=(str, ''),
    LDAP_REQUIRED_GROUPS=(list, []),
    LDAP_STAFF_GROUPS=(list, []),
    LDAP_SUPERUSER_GROUPS=(list, []),
    # API REST
    API_PREFIX=(str, 'api/v1/'),
)

# Load environment variables from .env (checks backend/.env and project root .env)
env_file = BASE_DIR / '.env'
if not env_file.exists() and (BASE_DIR.parent / '.env').exists():
    env_file = BASE_DIR.parent / '.env'

environ.Env.read_env(env_file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# Determinación de entorno (True = PostgreSQL / False = SQLite)
# Si PRODUCTION (o PRODUCCION) es True -> PostgreSQL
# Si es False -> SQLite
PRODUCTION = env.bool('PRODUCTION', default=env.bool('PRODUCCION', default=not DEBUG))

ALLOWED_HOSTS = env('ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')

# Prefijo y versionado de la API REST (configurable vía .env)
# Normaliza el string para asegurar que comience sin barra y termine en barra '/'
_api_prefix_raw = env('API_PREFIX', default='api/v1/').strip('/')
API_PREFIX = f"{_api_prefix_raw}/" if _api_prefix_raw else "api/v1/"

# ==============================================================================
# AUTENTICACIÓN SEGURA MEDIANTE TOKENS JWT
# ==============================================================================
JWT_SECRET_KEY = env('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ALGORITHM = env('JWT_ALGORITHM', default='HS256')
JWT_ACCESS_EXPIRATION_MINUTES = env.int('JWT_ACCESS_EXPIRATION_MINUTES', default=60)
JWT_REFRESH_EXPIRATION_DAYS = env.int('JWT_REFRESH_EXPIRATION_DAYS', default=7)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Dashboard.apps.DashboardConfig',
    'aplicativos.apps.AplicativosConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

if PRODUCTION:
    # Producción: PostgreSQL
    db_user = env('DB_USER', default='postgres')
    db_password = env('DB_PASSWORD', default='postgres')
    db_host = env('DB_HOST', default='localhost')
    db_port = env('DB_PORT', default='5432')
    db_name = env('DB_NAME', default='gestion_comercial')
    default_postgres_url = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    DATABASES = {
        'default': env.db('DATABASE_URL', default=default_postgres_url)
    }
    DATABASES['default']['CONN_MAX_AGE'] = env.int('DB_CONN_MAX_AGE', default=600)
else:
    # False / Desarrollo: SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    DATABASES['default']['CONN_MAX_AGE'] = env.int('DB_CONN_MAX_AGE', default=0)


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = env('LANGUAGE_CODE')

TIME_ZONE = env('TIME_ZONE')

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = env('STATIC_URL', default='static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = env('MEDIA_URL', default='media/')
MEDIA_ROOT = BASE_DIR / 'media'


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}


# ==============================================================================
# AUTENTICACIÓN ACTIVE DIRECTORY (AD / LDAP)
# ==============================================================================
LDAP_ENABLED = env('LDAP_ENABLED')
LDAP_SERVER_URI = env('LDAP_SERVER_URI')
LDAP_PORT = env('LDAP_PORT')
LDAP_USE_SSL = env('LDAP_USE_SSL')
LDAP_CONNECT_TIMEOUT = env('LDAP_CONNECT_TIMEOUT')
LDAP_DOMAIN = env('LDAP_DOMAIN')

LDAP_BIND_DN = env('LDAP_BIND_DN')
LDAP_BIND_PASSWORD = env('LDAP_BIND_PASSWORD')
LDAP_SEARCH_BASE = env('LDAP_SEARCH_BASE')

# Control de acceso por GPO / Grupos de seguridad de AD
# Si se definen grupos aquí, el usuario DEBE pertenecer a al menos uno para iniciar sesión
LDAP_REQUIRED_GROUPS = env('LDAP_REQUIRED_GROUPS')

# Mapeo de grupos de AD a permisos administrativos en Django
LDAP_STAFF_GROUPS = env('LDAP_STAFF_GROUPS')
LDAP_SUPERUSER_GROUPS = env('LDAP_SUPERUSER_GROUPS')

# Backends de autenticación: AD primero, con fallback al backend local de Django
AUTHENTICATION_BACKENDS = [
    'core.authentication.ActiveDirectoryBackend',
    'django.contrib.auth.backends.ModelBackend',
]
