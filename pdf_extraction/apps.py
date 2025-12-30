from django.apps import AppConfig


class PdfExtractionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pdf_extraction'
    verbose_name = 'PDF Extraction'

    def ready(self):
        # Import signals to ensure they are registered
        import pdf_extraction.signals  # noqa
