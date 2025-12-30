from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import PDFExtraction, PDFExtractionItem


class PDFExtractionItemInline(TabularInline):
    model = PDFExtractionItem
    extra = 1
    fields = ('pdf_file', 'pdf_file_name')
    readonly_fields = ('created_at', 'updated_at', 'pdf_file_name')


@admin.register(PDFExtraction)
class PDFExtractionAdmin(ModelAdmin):
    list_display = ('customer_name', 'customer_id', 'extraction_method', 'created_at', 'updated_at')
    list_filter = ('extraction_method', 'created_at')
    search_fields = ('customer_name', 'customer_id')
    readonly_fields = ('created_at', 'updated_at', 'total_token', 'input_token', 'output_token')

    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_id', 'customer_name'),
            'classes': ('tab',)
        }),
        ('Extraction Details', {
            'fields': ('extraction_method', 'model_used'),
            'classes': ('tab',)

        }),
        ('Token Usage', {
            'fields': ('input_token', 'output_token', 'total_token'),
            'classes': ('tab',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('tab',)
        }),
    )

    inlines = [PDFExtractionItemInline]

