from django.db import models


class CustomerRegexRule(models.Model):
    customer_id = models.CharField(max_length=100, null=True, blank=True)
    customer_name = models.CharField(max_length=255,
                                     choices=  (('Food Hall', 'Food Hall'),))
    field_name = models.CharField(max_length=255)
    regex_pattern = models.TextField()
    regex_pattern_v2 = models.TextField(null=True, blank=True)
    regex_pattern_v3 = models.TextField(null=True, blank=True)
    regex_group = models.IntegerField(null=True, blank=True, default=1)
    is_item_field = models.BooleanField(default=False)
    data_type = models.CharField(max_length=50, choices=(
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('date', 'Date'),
    ), default='string')

    def __str__(self):
        return f"{self.customer_name} - {self.field_name}"



class PPHRegexRule(models.Model):
    PPH_TYPE_CHOICES = (
        ('pph_masukan', 'PPH Masukan'),
        ('pph_keluaran', 'PPH Keluaran'),
    )
    
    pph_id = models.CharField(max_length=100, null=True, blank=True)
    pph_name = models.CharField(max_length=255, choices=PPH_TYPE_CHOICES)
    field_name = models.CharField(max_length=255)
    regex_pattern = models.TextField()
    regex_pattern_v2 = models.TextField(null=True, blank=True)
    regex_pattern_v3 = models.TextField(null=True, blank=True)
    regex_group = models.IntegerField(null=True, blank=True, default=1)
    is_item_field = models.BooleanField(default=False)
    data_type = models.CharField(max_length=50, choices=(
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('date', 'Date'),
    ), default='string')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'PPH Regex Rule'
        verbose_name_plural = 'PPH Regex Rules'

    def __str__(self):
        return f"{self.pph_name} - {self.field_name}"
