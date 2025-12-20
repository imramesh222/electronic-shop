from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages

class LoginRequiredMessageMixin(LoginRequiredMixin):
    """Verify that the current user is authenticated and show a message if not."""
    login_url = 'accounts:login'
    permission_denied_message = 'Please log in to access this page.'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, self.permission_denied_message)
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

class LoginRequiredToBuyMixin(LoginRequiredMixin):
    """Mixin to require login for purchase-related actions."""
    login_url = 'accounts:login'
    permission_denied_message = 'Please log in to complete your purchase.'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, self.permission_denied_message)
            if hasattr(self, 'get_success_url'):
                self.request.session['next'] = self.get_success_url()
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
