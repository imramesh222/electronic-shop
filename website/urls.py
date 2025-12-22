# website/urls.py
from django.urls import path
from . import views
from .views import ContactView

app_name = 'website'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('contact/', ContactView.as_view(), name='contact'),
]