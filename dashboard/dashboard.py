from django.contrib import admin
from django.db.models import Sum, Count, Avg
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from orders.models import Order, OrderItem
from products.models import Product, Category
import json

class RevenueDashboardAdmin(admin.ModelAdmin):
    change_list_template = 'admin/revenue_dashboard.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        # Calculate revenue statistics
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        this_year_start = today.replace(month=1, day=1)
        
        # Overall statistics
        total_orders = Order.objects.count()
        total_revenue = Order.objects.filter(is_paid=True).aggregate(total=Sum('total_price'))['total'] or 0
        pending_orders = Order.objects.filter(status='pending').count()
        processing_orders = Order.objects.filter(status='processing').count()
        
        # Today's statistics
        today_orders = Order.objects.filter(created_at__date=today).count()
        today_revenue = Order.objects.filter(created_at__date=today, is_paid=True).aggregate(total=Sum('total_price'))['total'] or 0
        
        # This month statistics
        this_month_orders = Order.objects.filter(created_at__gte=this_month_start).count()
        this_month_revenue = Order.objects.filter(created_at__gte=this_month_start, is_paid=True).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Last month statistics
        last_month_orders = Order.objects.filter(created_at__gte=last_month_start, created_at__lt=this_month_start).count()
        last_month_revenue = Order.objects.filter(created_at__gte=last_month_start, created_at__lt=this_month_start, is_paid=True).aggregate(total=Sum('total_price'))['total'] or 0
        
        # This year statistics
        this_year_orders = Order.objects.filter(created_at__gte=this_year_start).count()
        this_year_revenue = Order.objects.filter(created_at__gte=this_year_start, is_paid=True).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Top selling products
        top_products = OrderItem.objects.values('product__name').annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('price') * Sum('quantity')
        ).order_by('-total_sold')[:10]
        
        # Category performance
        category_performance = OrderItem.objects.values('product__category__name').annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('price') * Sum('quantity')
        ).order_by('-total_revenue')[:10]
        
        # Order status breakdown
        order_status_counts = Order.objects.values('status').annotate(count=Count('id'))
        
        # Monthly revenue trend (last 12 months)
        monthly_trend = []
        for i in range(12):
            month_start = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_orders = Order.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
            
            month_revenue = Order.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end,
                is_paid=True
            ).aggregate(total=Sum('total_price'))['total'] or 0
            
            monthly_trend.append({
                'month': month_start.strftime('%b %Y'),
                'orders': month_orders,
                'revenue': float(month_revenue)
            })
        
        monthly_trend.reverse()  # Show oldest to newest
        
        context = {
            **(extra_context or {}),
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'today_orders': today_orders,
            'today_revenue': today_revenue,
            'this_month_orders': this_month_orders,
            'this_month_revenue': this_month_revenue,
            'last_month_orders': last_month_orders,
            'last_month_revenue': last_month_revenue,
            'this_year_orders': this_year_orders,
            'this_year_revenue': this_year_revenue,
            'top_products': top_products,
            'category_performance': category_performance,
            'order_status_counts': order_status_counts,
            'monthly_trend': json.dumps(monthly_trend),
            'revenue_growth': self.calculate_growth(this_month_revenue, last_month_revenue),
            'order_growth': self.calculate_growth(this_month_orders, last_month_orders),
        }
        
        return super().changelist_view(request, context)
    
    def calculate_growth(self, current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('revenue-data/', self.admin_site.admin_view(self.get_revenue_data), name='revenue_data'),
        ]
        return custom_urls + urls
    
    def get_revenue_data(self, request):
        # Return JSON data for AJAX requests
        days = int(request.GET.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        data = []
        current_date = start_date
        while current_date <= end_date:
            day_revenue = Order.objects.filter(
                created_at__date=current_date,
                is_paid=True
            ).aggregate(total=Sum('total_price'))['total'] or 0
            
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'revenue': float(day_revenue)
            })
            current_date += timedelta(days=1)
        
        return JsonResponse({'data': data})

# Register a dummy model to host the dashboard
from django.db import models

class RevenueDashboard(models.Model):
    class Meta:
        verbose_name = "Revenue Dashboard"
        verbose_name_plural = "Revenue Dashboard"
        app_label = 'dashboard'
    
    def __str__(self):
        return "Revenue Dashboard"

@admin.register(RevenueDashboard)
class RevenueDashboardAdminView(RevenueDashboardAdmin):
    pass
