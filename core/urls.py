# core/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/', include('accounts.urls')),
    path('api/', include('products.urls')),
    path('api/orders/', include('orders.urls', namespace='orders')),
    path('api/cart/', include('cart.urls')),
    # Removed payment URL as the app doesn't exist
    path('', include('website.urls')),
]