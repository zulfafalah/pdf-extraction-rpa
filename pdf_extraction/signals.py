from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PDFExtractionItem
from .services import PDFExtractionService


@receiver(post_save, sender=PDFExtractionItem)
def handle_pdf_extraction_item_save(sender, instance: PDFExtractionItem, created: bool, **kwargs):
    # Only process extraction when item is first created, not on updates
    if created:
        pdf_service = PDFExtractionService()
        pdf_service.prosess_extraction(instance.pdf_extraction.id)

