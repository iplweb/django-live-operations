"""
Demo project settings for django-live-operations Phase 5 demo.

Env vars:
  REDIS_URL          — default redis://localhost:6379/0
  CELERY_BROKER_URL  — default same as REDIS_URL
  RUNNER             — override LIVE_OPERATIONS["RUNNER"] (default: "celery")
  SECRET_KEY         — override the dev key
  DEBUG              — default True
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "demo-insecure-key-change-in-production")

DEBUG = os.environ.get("DEBUG", "true").lower() not in ("0", "false", "no")

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "channels_broadcast",
    "live_operations",
    "demo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # LocaleMiddleware must sit after SessionMiddleware and before CommonMiddleware.
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "demo_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "demo_project.wsgi.application"
ASGI_APPLICATION = "demo_project.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # SQLITE_PATH lets the Docker web + worker containers share one SQLite
        # file on a named volume — without it each container has its own DB and
        # the worker can't see operations the web created. Local dev uses the
        # default path.
        "NAME": os.environ.get("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
    }
}

_redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Use the pub/sub channel layer, not the default list-based core layer: the
# core RedisChannelLayer's blocking receive raises "Timeout reading from redis"
# after redis-py's socket timeout on an idle consumer (channels_redis 4.x +
# redis-py 8.x). RedisPubSubChannelLayer is the right backend for group
# broadcasting (what channels_broadcast does) and does not exhibit this.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {"hosts": [_redis_url]},
    }
}

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", _redis_url)
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticroot"

# --- Internationalization ---------------------------------------------------
# The demo ships translations for every language django-live-operations
# supports. Pick one via the language switcher in the nav (POSTs to
# django.conf.urls.i18n's set_language view), or via Accept-Language.
LANGUAGE_CODE = "en"
USE_I18N = True
USE_TZ = True
LANGUAGES = [
    ("en", "English"),
    ("pl", "Polski"),
    ("uk", "Українська"),
    ("lt", "Lietuvių"),
    ("et", "Eesti"),
    ("de", "Deutsch"),
    ("fr", "Français"),
    ("zh-hans", "简体中文"),
    ("ja", "日本語"),
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
# Without this, Django defaults to /accounts/profile/ (which 404s) after login.
LOGIN_REDIRECT_URL = "/"

_runner = os.environ.get("RUNNER", "celery")
LIVE_OPERATIONS = {
    "BASE_TEMPLATE": "base.html",
    "RUNNER": _runner,
    "THROTTLE_HZ": 10,
}
