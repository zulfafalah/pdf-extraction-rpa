from django.db import models

# Create your models here.
class CustomerFieldMapping(models.Model):
    customer_id = models.CharField(max_length=100, null=True, blank=True)
    customer_name = models.CharField(max_length=255, choices=(
        ('Food Hall', 'Food Hall'),
    ))
    field_name = models.CharField(max_length=255, blank=True, null=True)
    origin_value = models.CharField(max_length=255, blank=True, null=True)
    destination_value = models.CharField(max_length=255, blank=True, null=True)
    is_field_item = models.BooleanField(default=False, verbose_name='Is Field Item')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=150, blank=True, null=True)
    updated_by = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        verbose_name = 'Customer Field Mapping'
        verbose_name_plural = 'Customer Field Mappings'

    def __str__(self):
        return f'{self.customer_name} - {self.origin_value} to {self.destination_value}'

