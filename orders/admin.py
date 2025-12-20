# orders/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'total_price']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'is_paid', 'total_price', 'created_at', 'view_order_items')
    list_filter = ('status', 'is_paid', 'created_at', 'updated_at')
    search_fields = ('user__email', 'id', 'shipping_address')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    list_editable = ('status', 'is_paid')
    date_hierarchy = 'created_at'
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def view_order_items(self, obj):
        return format_html('<a href="/admin/orders/order/{}/change/">View Items</a>', obj.id)
    view_order_items.short_description = 'Order Items'
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "Mark selected orders as Processing"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_as_shipped.short_description = "Mark selected orders as Shipped"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = "Mark selected orders as Delivered"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
    mark_as_cancelled.short_description = "Mark selected orders as Cancelled"
    
    def has_add_permission(self, request):
        return False