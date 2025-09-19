"""Django settings for the AdminOS Lab project.

This module centralises configuration around environment variables so the
application can move from local SQLite development to hosted PostgreSQL
instances without code changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import environ

# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent


def _project_path(value: Union[str, Path]) -> Path:
    """Return an absolute path rooted at ``BASE_DIR`` when relative paths are provided."""

    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    return candidate


# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=(str, "change-me"),
    DJANGO_ALLOWED_HOSTS=(list[str], ["localhost", "127.0.0.1"]),
)

_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(_env_file)

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "registers",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "adminos_lab.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "adminos_lab.wsgi.application"

# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}",
    )
}
DATABASES["default"].setdefault("ATOMIC_REQUESTS", True)

if DATABASES["default"]["ENGINE"].endswith("postgresql"):
    DATABASES["default"].setdefault("CONN_MAX_AGE", env.int("POSTGRES_CONN_MAX_AGE", default=60))
    DATABASES["default"].setdefault(
        "OPTIONS",
        {"connect_timeout": env.int("POSTGRES_CONNECT_TIMEOUT", default=5)},
    )

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static and media assets
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = _project_path(env("DJANGO_STATIC_ROOT", default="staticfiles"))
STATICFILES_DIRS = [_project_path("static")]

MEDIA_URL = "/media/"
MEDIA_ROOT = _project_path(env("DJANGO_MEDIA_ROOT", default="media"))

BACKUP_ROOT = _project_path(env("DJANGO_BACKUP_ROOT", default="backups"))
BACKUP_DATABASE_DIR = _project_path(
    env("DJANGO_BACKUP_DATABASE_DIR", default=str(BACKUP_ROOT / "database"))
)
BACKUP_MEDIA_DIR = _project_path(
    env("DJANGO_BACKUP_MEDIA_DIR", default=str(BACKUP_ROOT / "media"))
)

WEASYPRINT_BASEURL = env(
    "WEASYPRINT_BASEURL",
    default=str(_project_path("static")),
)
WEASYPRINT_TEMP_DIR = _project_path(env("WEASYPRINT_TEMP_DIR", default=".tmp/weasyprint"))
REPORTLAB_TEMP_DIR = _project_path(env("REPORTLAB_TEMP_DIR", default=".tmp/reportlab"))

# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
