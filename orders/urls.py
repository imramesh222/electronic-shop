# python
# File: `orders/urls.py`
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/invoice/', views.OrderInvoiceView.as_view(), name='invoice'),
    path('orders/<int:pk>/cancel/', views.OrderCancel.as_view(), name='order_cancel'),
    path('orders/<int:pk>/return/', views.OrderReturn.as_view(), name='order_return'),
]
