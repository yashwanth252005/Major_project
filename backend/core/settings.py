"""
Django settings for the Brain Tumor XAI backend.

This project intentionally does NOT touch anything inside Brain_Tumor_AI/.
It imports and calls that code from api/inference.py instead.
"""

import os
from pathlib import Path


# ============================================================
# BASE DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
# .../Major_project/backend

REPO_ROOT = BASE_DIR.parent
# .../Major_project

BRAIN_TUMOR_AI_DIR = REPO_ROOT / "Brain_Tumor_AI"
# .../Major_project/Brain_Tumor_AI


# ============================================================
# DJANGO BASIC SETTINGS
# ============================================================

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-secret-key-change-me"
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["*"]


# ============================================================
# GEMINI API SETTINGS
# ============================================================

# Gemini API key is read from the environment.
# DO NOT hardcode the actual API key here.
#
# Example environment variable:
# GEMINI_API_KEY=your_actual_gemini_api_key

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Model used only for checking whether the uploaded image
# appears to be a valid brain MRI.
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)


# ============================================================
# INSTALLED APPS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",

    "api",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]


# ============================================================
# URL / WSGI
# ============================================================

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

# SQLite is enough to persist scan history for this project.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================

# This project currently has no login/users.
# Therefore DRF does not authenticate incoming requests.

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny"
    ],
}


# ============================================================
# CORS
# ============================================================

# Allow the Vite frontend to communicate with Django
# during local development.

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


# ============================================================
# FILE UPLOAD LIMITS
# ============================================================

# Uploaded MRI scans can be a few MB.

DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
# 20 MB

FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
# 20 MB


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "static/"


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"