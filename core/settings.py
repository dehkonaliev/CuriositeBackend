from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


load_dotenv(os.path.join(BASE_DIR, '.env'))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG') == 'True'

ALLOWED_HOSTS = [
    'www.curiosite.uz',
    'curiosite.uz',
    'curiosite.up.railway.app',
    'localhost',
    '127.0.0.1',
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'https://www.curiosite.uz',
    'https://curiosite.uz',
    'https://curiosite.up.railway.app',
]

CSRF_TRUSTED_ORIGINS = [
    'https://www.curiosite.uz',
    'https://curiosite.uz',
    'https://curiosite.up.railway.app',
    'http://127.0.0.1:8000',
]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'whitenoise',
    
    'baseapp',
    'authentication',
    'courses',
    'profiles',
    'enrollments',
    'payments',
    'quizzes',
    'reviews',
    'notifications',
    'corsheaders',
    'certificates',
    'posts',
    'chat',
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

AUTHENTICATION_BACKENDS = [
    'authentication.backends.EmailOrPhoneBackend',   
    'django.contrib.auth.backends.ModelBackend'
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=5),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if not DEBUG:
    INSTALLED_APPS += ['storages']
    
    # Django 4.2+ new STORAGES API (use this if on 4.2+)
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')  # e.g. https://xxxx.railway.app
AWS_S3_REGION_NAME = os.environ.get('AWS_DEFAULT_REGION', 'auto')


AWS_S3_ADDRESSING_STYLE = 'path'  # important for most S3-compatible providers
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None  # let bucket policy control access instead of per-object ACLs
AWS_QUERYSTRING_AUTH = True  # set False if you want plain public URLs, True for signed/private URLs
AWS_S3_SIGNATURE_VERSION = 's3v4'




LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PGDATABASE'),
        'USER': os.environ.get('PGUSER'),
        'PASSWORD': os.environ.get('PGPASSWORD'),
        'HOST': os.environ.get('PGHOST'),
        'PORT': os.environ.get('PGPORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

AUTH_USER_MODEL = 'authentication.CustomUser'

EMAIL_EXPIRATION_TIME = 100
PHONE_EXPIRATION_TIME = 100

# Where password-reset links in emails point (the frontend app).
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

RESEND_API_KEY = os.environ.get('RESEND_API_KEY')

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / '/media/'

STATIC_URL = '/static/'

# Where collectstatic gathers all static files for production
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Where Django looks for your own static files during development
# (only needed if you have app-level static folders outside each app)
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
