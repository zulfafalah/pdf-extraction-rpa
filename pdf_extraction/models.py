from django.db import models

class PDFExtraction(models.Model):
    customer_id = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=150)
    updated_by = models.CharField(max_length=150)

    extraction_method = models.CharField(max_length=100, default='regex',choices=[('regex', 'Regex Based Extraction'), ('ai', 'AI Based Extraction')])
    model_used = models.CharField(max_length=150, blank=True)
    input_token = models.IntegerField(default=0)
    output_token = models.IntegerField(default=0)
    total_token = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Extraction'
        verbose_name_plural = 'Extractions'

    def __str__(self):
        return f'{self.customer_name}'


class PDFExtractionItem(models.Model):
    pdf_extraction = models.ForeignKey('PDFExtraction', on_delete=models.CASCADE, related_name='pdf_items')
    pdf_file_name = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to='pdf/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=150)
    updated_by = models.CharField(max_length=150)

    def __str__(self):
        return self.pdf_file.name
