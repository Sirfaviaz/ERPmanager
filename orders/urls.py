from django.urls import path
from . import views

urlpatterns = [

    # =======================
    # 📤 Order Upload & Save
    # =======================
    path('upload/', views.extract_order_view, name='extract_order'),
    path('save/', views.save_order_view, name='save_order'),
    path('push-to-google/', views.push_to_google_sheet_view, name='push_to_google'),

    # =======================
    # 📋 Order Management
    # =======================
    path('list/', views.order_list_view, name='order_list'),
    path('orders/update/<int:order_id>/', views.update_order_view, name='update_order'),
    path('orders/delete/<int:order_id>/', views.delete_order_view, name='delete_order'),
    path('mark-delivered/<int:order_id>/', views.mark_order_delivered, name='mark_delivered'),

    # =======================
    # 🔍 ERP Integration
    # =======================
    path('erp/search-item/', views.erp_item_search_page, name='erp_search_page'),
    path('erp/ajax/search/', views.erp_item_suggestions, name='erp_item_suggestions'),
    path('erp/ajax/item-details/', views.erp_item_details, name='erp_item_details'),
]
