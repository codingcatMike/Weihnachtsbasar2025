"""
Django settings for Basar project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SITE_URL = "https://webdevcode.de"

SECRET_KEY = "django-insecure-ed%gkrmb9^7wd9rssu*0gwvp%3e2dept3mdx6o2v4^uzqu$to4"

DEBUG = True
MAINTENANCE_PASSWORD = "main"


ALLOWED_HOSTS = [
    "webdevcode.de",
    "www.webdevcode.de",
    "127.0.0.1",
    "localhost",
]

CSRF_TRUSTED_ORIGINS = [
    "https://webdevcode.de",
    "https://www.webdevcode.de",
]

# -------------------
# Static & Media Files
# -------------------

STATIC_URL = "/static/"

# Wichtiger Ordner, wo collectstatic ALLES sammelt
STATIC_ROOT = BASE_DIR / "staticfiles"

# Dein App-Ordner "main/static" bleibt hiermit sichtbar
STATICFILES_DIRS = [
    BASE_DIR / "main" / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------
# Applications
# -------------------

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main",
    "channels",
]

ASGI_APPLICATION = "Basar.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis-server-ip", 6379)],
        },
    },
}


# -------------------
# Middleware & Templates
# -------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "main.middleware.MaintenanceModeMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "Basar.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Basar.wsgi.application"

# -------------------
# Database
# -------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -------------------
# Password validation
# -------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------
# Internationalization
# -------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------
# Defaults
# -------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
