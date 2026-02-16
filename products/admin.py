from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'product_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('product_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(product_count=Count('products'))
    
    def product_count(self, obj):
        count = obj.products.count()
        return format_html('<span style="font-weight: bold; color: #2e7d32;">{}</span>', count)
    product_count.short_description = 'Products'
    product_count.admin_order_field = 'product_count'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'available', 'image_preview', 'created_at')
    list_filter = ('available', 'category', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    list_editable = ('price', 'stock', 'available')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock', 'available')
        }),
        ('Media', {
            'fields': ('image', 'image_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'
    
    def category_name(self, obj):
        return obj.category.name
    category_name.short_description = 'Category'
    
    def available_products(self, obj):
        return obj.stock > 0
    available_products.boolean = True
    available_products.short_description = 'In Stock'
