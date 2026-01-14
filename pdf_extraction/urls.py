from django.urls import path
from .views import PDFTextExtractionView, PDFUploadAndExportView, ExportToExcelView, CustomerListView, UploadAndExportMultiView

app_name = "pdf_extraction"

urlpatterns = [
    path('extract-text/', PDFTextExtractionView.as_view(), name='extract-text'),
    path('upload-and-export/', PDFUploadAndExportView.as_view(), name='upload-and-export'),
    path('export-excel/', ExportToExcelView.as_view(), name='export-excel'),
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('upload-and-export-multi/', UploadAndExportMultiView.as_view(), name='upload-and-export-multi'),

]
