# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from django.views.generic import TemplateView

app_name = 'accounts'

urlpatterns = [
    # API Endpoints
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Registration (handles both GET and POST)
    path('register/', views.RegisterView.as_view(), name='register'),
    path('api/register/', views.RegisterView.as_view(), name='api_register'),
    
    # User Profile
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Authentication Views
    path('login/', views.CustomLoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.CustomLogoutView.as_view(next_page='website:home'), name='logout'),
]