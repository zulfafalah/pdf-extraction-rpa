from django.urls import path
from .views import PDFTextExtractionView

app_name = "pdf_extraction"

urlpatterns = [
    path('extract-text/', PDFTextExtractionView.as_view(), name='extract-text'),
]
