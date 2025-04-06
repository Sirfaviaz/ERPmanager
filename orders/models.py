# orders/models.py

from django.db import models
class Order(models.Model):
    source = models.CharField(max_length=50)  # Rafeeq or Snoonu
    order_number = models.CharField(max_length=50, unique=True)
    order_date = models.DateField(null=True, blank=True)  
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)
    google_location = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.source} - {self.customer_name or self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    substituted_item_code = models.CharField(max_length=100, blank=True)  # From ERPNext
    from_outside = models.BooleanField(default=False)
    external_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    external_bill = models.FileField(upload_to='external_bills/', null=True, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.product_name
