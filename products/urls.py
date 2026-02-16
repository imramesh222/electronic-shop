# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'products'

# API Router
api_router = DefaultRouter()
api_router.register(r'categories', views.CategoryViewSet, basename='category')
api_router.register(r'products', views.ProductViewSet, basename='product')

urlpatterns = [
    # Frontend URLs - specific paths first
    path('', views.ProductListView.as_view(), name='product_list'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Cart actions
    path('<slug:slug>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('<slug:slug>/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('<slug:slug>/update-quantity/', views.update_quantity, name='update_quantity'),
    
    # API URLs - moved to the end to avoid conflicts
    path('api/', include(api_router.urls)),
]