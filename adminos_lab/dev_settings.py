"""Development-only Django settings for the AdminOS Lab project."""

from __future__ import annotations

from .settings import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = env.list(  # type: ignore[name-defined]
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "0.0.0.0"],
)
CSRF_TRUSTED_ORIGINS = env.list(  # type: ignore[name-defined]
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=[f"http://{host}:8000" for host in ALLOWED_HOSTS if host != "127.0.0.1"],
)

DATABASES["default"] = env.db(  # type: ignore[name-defined]
    "DATABASE_URL",
    default=f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}",
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
INTERNAL_IPS = ["127.0.0.1"]
