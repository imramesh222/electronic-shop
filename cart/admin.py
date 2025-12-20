# cart/admin.py
from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ['product', 'quantity', 'total_price']
    readonly_fields = ['total_price']
    can_delete = False

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'id')
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        return False

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'total_price')
    search_fields = ('product__name', 'cart__id')
    readonly_fields = ('total_price',)
    list_select_related = ('product', 'cart')