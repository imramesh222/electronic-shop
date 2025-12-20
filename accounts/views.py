from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserRegistrationSerializer, 
    UserProfileSerializer, 
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer
)
from django.contrib.auth.views import LoginView, LogoutView

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('website:home')
    
    def get_success_url(self):
        # Get the next URL from the request parameters or use the default success_url
        return self.request.POST.get('next', self.request.GET.get('next', str(self.success_url)))
    
    def form_valid(self, form):
        # Save the user first
        user = form.save(commit=False)
        user.username = form.cleaned_data['email']  # Use email as username
        user.save()
        
        # Log the user in after successful registration
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'Welcome to Electronic Shop, {user.name}!')
        return super().form_valid(form)
        return super().form_valid(form)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    model = User

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response(
                {"message": "Password updated successfully"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    next_page = 'website:home'
    
    def get_success_url(self):
        # Get the next URL from the request parameters or use the default next_page
        return self.request.POST.get('next', self.request.GET.get('next', self.next_page))
    
    def post(self, request, *args, **kwargs):
        # Override post method to handle email-based authentication
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.name}!')
            return redirect(self.get_success_url())
        else:
            messages.error(request, 'Invalid email or password')
            return self.render_to_response(self.get_context_data())
class CustomLogoutView(LogoutView):
    next_page = 'website:home'