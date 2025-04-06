# project/urls.py

from django.urls import path, include

urlpatterns = [
    
    path('orders/', include(('orders.urls', 'orders'), namespace='orders')),
]
