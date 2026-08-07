"""
Django settings for the Brain Tumor XAI backend.

This project intentionally does NOT touch anything inside Brain_Tumor_AI/.
It imports and calls that code from api/inference.py instead.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent          # .../backend
REPO_ROOT = BASE_DIR.parent                                 # .../Major_project (repo root)
BRAIN_TUMOR_AI_DIR = REPO_ROOT / "Brain_Tumor_AI"            # friend's untouched folder

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-me")

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",       # DRF's request.user / AnonymousUser needs this
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# SQLite is enough to persist scan history for this project
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# This project has no login/users, so tell DRF not to try to authenticate
# requests (its defaults otherwise pull in django.contrib.auth, which isn't
# in INSTALLED_APPS here and would error out, as you just saw).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

# CORS - allow the Vite dev server to call the API during development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Uploaded MRI scans can be a few MB - raise the default limits a bit
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024   # 20 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
