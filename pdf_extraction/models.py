from django.db import models


class PDFExtraction(models.Model):
    customer_id = models.CharField(max_length=100, null=True, blank=True)
    customer_name = models.CharField(max_length=255, choices=(
        ('Food Hall', 'Food Hall'),
    ))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=150, blank=True, null=True)
    updated_by = models.CharField(max_length=150, blank=True, null=True)

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
    pdf_file_name = models.CharField(max_length=255, blank=True)
    pdf_file = models.FileField(upload_to='pdf/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=150, null=True, blank=True)
    updated_by = models.CharField(max_length=150, null=True, blank=True )
    result_data = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = 'PDF Extraction Item'
        verbose_name_plural = 'PDF Extraction Items'

    def __str__(self):
        return self.pdf_file.name

    def extract_file_name(self):
        if self.pdf_file:
            import os
            filename = os.path.basename(self.pdf_file.name)
            self.pdf_file_name = filename
            return filename
        return None

    def save(self, *args, **kwargs):
        self.full_clean()
        print(f"Saving PDFExtractionItem id={self.id}")

        # Extract and set file name before saving
        if self.pdf_file:
            self.extract_file_name()

        super().save(*args, **kwargs)
