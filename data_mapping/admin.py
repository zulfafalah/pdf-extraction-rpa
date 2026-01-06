from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import CustomerFieldMapping


@admin.register(CustomerFieldMapping)
class CustomerFieldMappingAdmin(ModelAdmin):
    list_display = ('customer_name', 'customer_id', 'field_name', 'origin_value', 'destination_value', 'is_field_item', 'created_by', 'updated_by', 'created_at', 'updated_at')
    list_filter = ('customer_name', 'created_at')
    search_fields = ('customer_name', 'customer_id', 'field_name', 'origin_value', 'destination_value')
    readonly_fields = ('created_at', 'updated_at')
    exclude = ('created_by', 'updated_by')

    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_id', 'customer_name'),
        }),
        ('Field Mapping', {
            'fields': ('field_name', 'origin_value', 'destination_value', 'is_field_item'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if request.user and request.user.is_authenticated:
            if not change:
                obj.created_by = request.user.username
            obj.updated_by = request.user.username
        super().save_model(request, obj, form, change)
