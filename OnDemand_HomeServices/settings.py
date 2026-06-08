# Django settings for OnDemand_HomeServices project.
# Updated for Render deployment: DJ_DATABASE_URL, WhiteNoise, static handling, env-config.

import os
from pathlib import Path
import dj_database_url

RAZORPAY_KEY_ID = "rzp_test_SzAkKFhvRURgl5"
RAZORPAY_KEY_SECRET = "8xg7RyPjS2qt47Odq0hjwJvc"

# 1) Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# 2) Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-CHANGE_ME_FOR_PRODUCTION')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'smarturs.team@gmail.com'
EMAIL_HOST_PASSWORD = 'sflx ytuz ikdt osgp'  # Use an app password for Gmail

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# 3) Installed apps
INSTALLED_APPS = [
    'daphne',  # ASGI server — required for WebSocket support
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',  # your app
    'channels',
]

# 4) Middleware, include WhiteNoise early
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

# 5) URL and WSGI
ROOT_URLCONF = 'OnDemand_HomeServices.urls'
WSGI_APPLICATION = 'OnDemand_HomeServices.wsgi.application'
ASGI_APPLICATION = 'OnDemand_HomeServices.asgi.application'

# 6) Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.add_today_variable',
                'core.context_processors.notification_counts',
                'core.context_processors.razorpay_settings',
            ],
        },
    },
]

# 7) Database
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}
# 8) Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# 9) Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

REDIS_URL = os.environ.get("REDIS_URL", None)

# ─── Django Channels (WebSockets) ────────────────────────────────────────────
# For development, use in-memory channel layer if Redis is not configured
# For production, set REDIS_URL environment variable
if REDIS_URL and REDIS_URL.lower() != "memory":
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        },
    }
else:
    # Development: use in-memory channel layer (no Redis required)
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }

# ─── Celery + Redis (background tasks) ───────────────────────────────────────
CELERY_BROKER_URL = REDIS_URL if REDIS_URL else "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
# Set USE_CELERY_WORKER=True in production with Redis + celery worker running
USE_CELERY_WORKER = os.environ.get("USE_CELERY_WORKER", "False") == "True"
CELERY_TASK_ALWAYS_EAGER = not USE_CELERY_WORKER
CELERY_TASK_EAGER_PROPAGATES = True

# 10) Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [ BASE_DIR / 'static' ]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 11) Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 12) Media (invoice PDFs)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# GST rate for invoices (18%)
GST_RATE = 0.18
