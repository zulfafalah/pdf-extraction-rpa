"""Utility functions for Unfold Django Admin customization."""

import os

from django.contrib.auth import get_user_model

User = get_user_model()


def environment_callback(request):
    """Return the environment name based on DJANGO_SETTINGS_MODULE."""
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")

    if "production" in settings_module:
        return "production"
    elif "local" in settings_module:
        return "local"
    elif "test" in settings_module:
        return "test"

    return "development"


def environment_title_prefix_callback(request):
    """Return title prefix based on environment."""
    env = environment_callback(request)

    prefixes = {
        "production": "PROD",
        "local": "DEV",
        "test": "TEST",
        "development": "DEV",
    }

    return prefixes.get(env, "")


def user_count_badge(request):
    """Return the count of active users."""
    return User.objects.filter(is_active=True).count()


def extraction_count_badge(request):
    """Return the count of PDF extractions."""
    from pdf_extraction.models import PDFExtraction

    return PDFExtraction.objects.count()


def is_superuser(request):
    """Check if user is superuser."""
    return request.user.is_superuser
