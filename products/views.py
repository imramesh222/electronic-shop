from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from cart.models import Cart, CartItem 
from django.views.generic import ListView
from .models import Category

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    lookup_field = 'slug'
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(available=True)
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'available']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    lookup_field = 'slug'
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset
    
    @action(detail=True, methods=['post'])
    def add_stock(self, request, slug=None):
        product = self.get_object()
        quantity = request.data.get('quantity', 0)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {"quantity": ["Quantity must be greater than zero."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            product.stock += quantity
            product.save()
            return Response(ProductSerializer(product).data)
        except (ValueError, TypeError):
            return Response(
                {"quantity": ["A valid integer is required."]},
                status=status.HTTP_400_BAD_REQUEST
            )

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    query_pk_and_slug = True
    def get_queryset(self):
        return Product.objects.filter(available=True)

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        return Product.objects.filter(available=True).order_by('-created_at')

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'
    def get_queryset(self):
        return Category.objects.filter(is_active=True)
# Add these function-based views for cart actions
@require_POST
def add_to_cart(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    product = get_object_or_404(Product, slug=slug, available=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return JsonResponse({'message': 'Product added to cart'})
@require_POST
def remove_from_cart(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    cart_item = get_object_or_404(
        CartItem, 
        cart__user=request.user, 
        product__slug=slug
    )
    cart_item.delete()
    
    return JsonResponse({'message': 'Product removed from cart'})
@require_POST
def update_quantity(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    quantity = request.POST.get('quantity', 1)
    try:
        quantity = int(quantity)
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid quantity'}, status=400)
    
    cart_item = get_object_or_404(
        CartItem, 
        cart__user=request.user, 
        product__slug=slug
    )
    cart_item.quantity = quantity
    cart_item.save()
    
    return JsonResponse({'message': 'Quantity updated'})

class CategoryListView(ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'