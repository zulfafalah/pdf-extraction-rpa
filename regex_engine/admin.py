from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import CustomerRegexRule


@admin.register(CustomerRegexRule)
class CustomerRegexRuleAdmin(ModelAdmin):
    list_display = ('customer_name', 'customer_id', 'field_name', 'regex_pattern', 'regex_group')
    list_filter = ('customer_name', 'field_name')
    search_fields = ('customer_name', 'customer_id', 'field_name')

    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_id', 'customer_name'),
            'classes': ('tab',)
        }),
        ('Regex Configuration', {
            'fields': ('field_name', 'regex_pattern', 'regex_group'),
            'classes': ('tab',)
        }),
    )
