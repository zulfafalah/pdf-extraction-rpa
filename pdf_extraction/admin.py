from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import PDFExtraction, PDFExtractionItem


class PDFExtractionItemInline(TabularInline):
    model = PDFExtractionItem
    extra = 1
    fields = ('pdf_file', 'pdf_file_name', 'result_data')
    readonly_fields = ('created_at', 'updated_at', 'pdf_file_name', 'result_data')
    exclude = ('created_by', 'updated_by')


@admin.register(PDFExtraction)
class PDFExtractionAdmin(ModelAdmin):
    list_display = ('customer_name', 'customer_id', 'extraction_method', 'created_by', 'updated_by', 'created_at', 'updated_at')
    list_filter = ('extraction_method', 'created_at')
    search_fields = ('customer_name', 'customer_id')
    readonly_fields = ('created_at', 'updated_at', 'total_token', 'input_token', 'output_token')
    exclude = ('created_by', 'updated_by')

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

    def save_model(self, request, obj, form, change):

        if request.user and request.user.is_authenticated:
            if not change:
                obj.created_by = request.user
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """Set created_by and updated_by for PDFExtractionItem (inline)"""
        instances = formset.save(commit=False)
        for instance in instances:
            is_new = not instance.pk

            if request.user and request.user.is_authenticated:

                if is_new:
                    instance.created_by = request.user

                instance.updated_by = request.user

            instance.save()

        # Handle deleted objects
        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()
