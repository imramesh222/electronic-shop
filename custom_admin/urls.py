from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    path('', views.dashboard, name='dashboard'),
    
    # Users
    path('users/', views.users_list, name='users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    
    # Orders
    path('orders/', views.orders_list, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Products
    path('products/', views.products_list, name='products'),
    path('products/add/', views.products_list, name='add_product'),
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    
    # Categories
    path('categories/', views.categories_list, name='categories'),
    path('categories/add/', views.categories_list, name='add_category'),
    path('categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
]
