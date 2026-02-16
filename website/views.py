# website/views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from products.models import Product, Category

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'website/home.html'
    login_url = 'accounts:login'
    redirect_field_name = 'next'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['featured_products'] = Product.objects.filter(available=True)[:8]
            context['new_arrivals'] = Product.objects.filter(available=True).order_by('-created_at')[:8]
            # Add categories with default icons
            categories = list(Category.objects.all()[:6])
            default_icons = ['fas fa-laptop', 'fas fa-mobile-alt', 'fas fa-headphones', 'fas fa-camera', 'fas fa-tablet-alt', 'fas fa-desktop']
            for i, category in enumerate(categories):
                if not category.icon:
                    category.icon = default_icons[i % len(default_icons)]
            context['categories'] = categories
        return context
        
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and self.request.GET.get('next'):
            messages.info(request, 'Please log in to access the requested page.')
        return super().dispatch(request, *args, **kwargs)


class ContactView(TemplateView):
    template_name = 'website/contact.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('page_title', 'Contact Us')
        return ctx

