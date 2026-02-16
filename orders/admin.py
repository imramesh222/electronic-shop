# orders/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'total_price']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'status', 'is_paid', 'status_badge', 'is_paid_badge', 'total_price', 'item_count', 'created_at', 'actions_column')
    list_filter = ('status', 'is_paid', 'created_at', 'updated_at')
    search_fields = ('user__email', 'id', 'shipping_address')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at', 'total_price', 'item_count', 'revenue_display')
    list_editable = ('status', 'is_paid')
    date_hierarchy = 'created_at'
    actions = ['accept_orders', 'reject_orders', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'is_paid', 'total_price', 'item_count')
        }),
        ('Shipping Details', {
            'fields': ('shipping_address',)
        }),
        ('Revenue Information', {
            'fields': ('revenue_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').annotate(item_count=Count('items'))
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Customer Email'
    user_email.admin_order_field = 'user__email'
    
    def item_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    item_count.short_description = 'Items'
    item_count.admin_order_field = 'item_count'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ff9800',
            'processing': '#2196f3',
            'shipped': '#9c27b0',
            'delivered': '#4caf50',
            'cancelled': '#f44336'
        }
        color = colors.get(obj.status, '#757575')
        return format_html('<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def is_paid_badge(self, obj):
        if obj.is_paid:
            return format_html('<span style="background-color: #4caf50; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">Paid</span>')
        else:
            return format_html('<span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">Unpaid</span>')
    is_paid_badge.short_description = 'Payment'
    is_paid_badge.admin_order_field = 'is_paid'
    
    def actions_column(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<button class="button" onclick="acceptOrder({})" style="background: #4caf50; color: white; border: none; padding: 5px 10px; margin-right: 5px; cursor: pointer;">Accept</button>'
                '<button class="button" onclick="rejectOrder({})" style="background: #f44336; color: white; border: none; padding: 5px 10px; cursor: pointer;">Reject</button>',
                obj.id, obj.id
            )
        return format_html('<span style="color: #666;">No actions</span>')
    actions_column.short_description = 'Actions'
    
    def revenue_display(self, obj):
        if obj.is_paid:
            return format_html('<span style="color: #4caf50; font-weight: bold; font-size: 16px;">${}</span>', obj.total_price)
        else:
            return format_html('<span style="color: #f44336;">${} (Unpaid)</span>', obj.total_price)
    revenue_display.short_description = 'Revenue'
    
    def accept_orders(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='processing', updated_at=timezone.now())
        self.message_user(request, f'{updated} orders accepted and marked as processing.')
    accept_orders.short_description = "Accept selected orders"
    
    def reject_orders(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='cancelled', updated_at=timezone.now())
        self.message_user(request, f'{updated} orders rejected and marked as cancelled.')
    reject_orders.short_description = "Reject selected orders"
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing', updated_at=timezone.now())
    mark_as_processing.short_description = "Mark selected orders as Processing"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped', updated_at=timezone.now())
    mark_as_shipped.short_description = "Mark selected orders as Shipped"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered', updated_at=timezone.now())
    mark_as_delivered.short_description = "Mark selected orders as Delivered"
    
    def has_add_permission(self, request):
        return False
    
    class Media:
        js = ['admin/js/jquery.init.js']
        css = {
            'all': ('admin/css/custom_admin.css',)
        }