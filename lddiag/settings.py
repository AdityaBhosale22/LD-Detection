import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env file if present (ignored in git). Real environment variables win.
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
	return os.environ.get(name, "1" if default else "0").strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
	return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# Local development defaults to DEBUG on; containers set DJANGO_DEBUG=0.
DEBUG = env_bool("DJANGO_DEBUG", default=True)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
	if DEBUG:
		SECRET_KEY = "dev-only-insecure-secret-key"
	else:
		raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG=0")

# localhost entries are always allowed so the container health check works.
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "*" if DEBUG else "") + ["localhost", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	"rest_framework",
	"crispy_forms",
	"crispy_bootstrap5",
	"accounts",
	"assessments",
	"predictions",
	"recommendations",
	"reports",
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
]

ROOT_URLCONF = "lddiag.urls"

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

WSGI_APPLICATION = "lddiag.wsgi.application"
ASGI_APPLICATION = "lddiag.asgi.application"

# SQLite by default; docker-compose switches to PostgreSQL via DB_* variables.
DATABASES = {
	"default": {
		"ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
		"NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
		"USER": os.environ.get("DB_USER", ""),
		"PASSWORD": os.environ.get("DB_PASSWORD", ""),
		"HOST": os.environ.get("DB_HOST", ""),
		"PORT": os.environ.get("DB_PORT", ""),
		"CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
	}
}

AUTH_PASSWORD_VALIDATORS = [
	{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
	{"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
	{"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
	{"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
	"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
	"staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

AUTH_USER_MODEL = "accounts.UserAccount"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# --- AWS -------------------------------------------------------------------
# When AWS_S3_REPORTS_BUCKET is set, every generated PDF report is archived to S3.
# Credentials come from the standard boto3 chain (EC2 instance role in production).
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
AWS_S3_REPORTS_BUCKET = os.environ.get("AWS_S3_REPORTS_BUCKET", "")

# --- Logging: everything to stdout so `docker logs` / CloudWatch pick it up --
LOGGING = {
	"version": 1,
	"disable_existing_loggers": False,
	"formatters": {
		"standard": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
	},
	"handlers": {
		"console": {"class": "logging.StreamHandler", "formatter": "standard"},
	},
	"root": {"handlers": ["console"], "level": "INFO"},
	"loggers": {"botocore": {"level": "WARNING"}},
}
