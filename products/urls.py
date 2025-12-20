# products/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'products'  # Add this line

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # Frontend URLs
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),

    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Cart actions
    path('products/<slug:slug>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('products/<slug:slug>/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('products/<slug:slug>/update-quantity/', views.update_quantity, name='update_quantity'),
]