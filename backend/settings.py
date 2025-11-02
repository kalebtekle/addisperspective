from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key')

DEBUG = False

ALLOWED_HOSTS = ['192.168.1.11', '192.168.1.6','localhost', '127.0.0.1', 'addisperspective.onrender.com']


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'social_django',
    "graphene_django",
    "graphql_jwt",
    "corsheaders",
    "django_extensions",
    "blog",
    "django_vite",
    "tinymce",
    
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "allauth.account.middleware.AccountMiddleware",

]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

DJANGO_VITE = {
  "default": {
    "dev_mode": True
  }
}

DATABASES = {
    "default": {
        # "ENGINE": "django.db.backends.sqlite3",
        # "NAME": BASE_DIR / "db.sqlite3",
        dj_database_url.config(default=os.environ.get('DATABASE_URL'))
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Set the session cookie age in seconds (default is 1209600 seconds, or 2 weeks)
SESSION_COOKIE_AGE = 1209600

# Set whether the session expires when the user closes the browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


STATICFILES_DIRS = [
  os.path.join(BASE_DIR, 'static'),
  
  ]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


GRAPHENE = {
    "SCHEMA": "blog.schema.schema",
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}


#SITE_ID = 1 # Required for django-allauth

AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
    'blog.authentication.EmailBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'social_core.backends.google.GoogleOAuth2',
]

'''SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = "your-google-client-id"
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "your-google-client-secret" '''

# CORS settings

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
]

CSRF_COOKIE_HTTPONLY = False  # allow frontend to read the cookie
CSRF_COOKIE_SAMESITE = 'Lax'  # or 'None' for cross-origin with HTTPS
CSRF_COOKIE_SECURE = False    # True in production (with HTTPS)

# Optional: CORS headers (optional if already using django-cors-headers)
CORS_ALLOW_HEADERS = [
    'authorization',
    'content-type',
    'x-csrftoken',
    'x-requested-with',
]



VITE_PROJECT_ROOT = BASE_DIR / 'frontend'
VITE_ASSETS_URL = 'http://localhost:3000/'  # URL of your Vite development server
VITE_ASSETS_MANIFEST = 'http://localhost:3000/@vite/client/assets-manifest.json'  # URL of your Vite assets manifest


TINYMCE_DEFAULT_CONFIG = {
    'height': 360,
    'width': 800,
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'selector': 'textarea',
    'theme': 'modern',
    'plugins': '''
        textcolor save link image media preview codesample contextmenu
        table code lists fullscreen  insertdatetime  nonbreaking
        contextmenu directionality searchreplace wordcount visualblocks
        visualchars code fullscreen autolink lists  charmap print  hr
        anchor pagebreak
    ''',
    'toolbar1': '''
        fullscreen preview bold italic underline | fontselect,
        fontsizeselect  | forecolor backcolor | alignleft alignright |
        aligncenter alignjustify | indent outdent | bullist numlist table |
        | link image media | codesample |
    ''',
    'toolbar2': '''
        visualblocks visualchars |
        charmap hr pagebreak nonbreaking anchor |  code |
    ''',
    'contextmenu': 'formats | link image',
    'menubar': True,
    'statusbar': True,
}
