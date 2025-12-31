from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin
from .models import CustomerRegexRule


@admin.register(CustomerRegexRule)
class CustomerRegexRuleAdmin(ModelAdmin):
    list_display = ('customer_name', 'customer_id', 'field_name', 'regex_pattern', 'regex_group', 'is_item_field')
    list_filter = ('customer_name', 'field_name')
    search_fields = ('customer_name', 'customer_id', 'field_name')
    actions = ['duplicate_rows']

    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_id', 'customer_name'),
            'classes': ('tab',)
        }),
        ('Regex Configuration', {
            'fields': ('field_name', 'is_item_field', 'regex_pattern', 'regex_group'),
            'classes': ('tab',)
        }),
        ('Regex Additional Patterns', {
            'fields': ('regex_pattern_v2', 'regex_pattern_v3'),
            'classes': ('tab',)
        }),
    )

    def duplicate_rows(self, request, queryset):
        """
        Action for duplicating selected rows
        """
        duplicated_count = 0
        last_duplicated_obj = None

        for obj in queryset:
            # Save original ID before duplication
            obj.pk = None
            obj.id = None
            # Save new object (duplicate)
            obj.save()
            duplicated_count += 1
            last_duplicated_obj = obj

        # If only 1 row is duplicated, redirect to the edit page
        if duplicated_count == 1 and last_duplicated_obj:
            self.message_user(
                request,
                f'Row successfully duplicated. You are now editing the duplicate.',
                messages.SUCCESS
            )
            # Redirect to the edit page of the newly duplicated object
            url = reverse('admin:regex_engine_customerregexrule_change', args=[last_duplicated_obj.pk])
            return redirect(url)

        # If more than 1 row, show a regular success message
        self.message_user(
            request,
            f'{duplicated_count} rows successfully duplicated.',
            messages.SUCCESS
        )

    duplicate_rows.short_description = "Duplicate selected rows"
