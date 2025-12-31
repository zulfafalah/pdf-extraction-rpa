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

    def __str__(self):
        return f"{self.customer_name} - {self.field_name}"
