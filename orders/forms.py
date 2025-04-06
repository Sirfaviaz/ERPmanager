# orders/forms.py

from django import forms

from .models import Order

class BillUploadForm(forms.Form):
    bill_file = forms.FileField(label="Upload Bill")
    


from django.forms import modelformset_factory
from .models import Order, OrderItem

# Order Form
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['source', 'customer_name', 'customer_address', 'customer_phone', 'order_number', 'order_date', 'is_delivered']

# OrderItem Form
class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product_name', 'quantity', 'substituted_item_code', 'from_outside', 'external_cost', 'driver_name']

# Inline Formset (tie items to order)
OrderItemFormSet = modelformset_factory(
    OrderItem,
    form=OrderItemForm,
    extra=0,
    can_delete=True
)