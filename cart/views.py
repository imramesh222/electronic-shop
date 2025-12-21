# cart/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView
from django.contrib import messages
from django.urls import reverse_lazy
from core.mixins import LoginRequiredToBuyMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from products.models import Product
from .cart import Cart

class CartViewSet(LoginRequiredToBuyMixin, viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related('items__product')

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response(self.get_serializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response(
                {"error": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            cart_item = cart.items.get(product_id=product_id)
            cart_item.delete()
            return Response(self.get_serializer(cart).data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Product not found in cart"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        
        if not all([product_id, quantity is not None]):
            return Response(
                {"error": "Both product_id and quantity are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            cart_item = cart.items.get(product_id=product_id)
            if int(quantity) <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()
            return Response(self.get_serializer(cart).data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Product not found in cart"},
                status=status.HTTP_404_NOT_FOUND
            )

class CartDetailView(LoginRequiredToBuyMixin, DetailView):
    model = Cart
    template_name = 'cart/cart_detail.html'
    context_object_name = 'cart'
    login_url = 'accounts:login'
    
    def get_object(self):
        return get_object_or_404(Cart, user=self.request.user)
        
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to view your cart.')
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


@login_required
def cart_detail(request):
    cart = Cart(request)
    cart_items = cart.get_cart_items()
    cart_total = cart.get_total_price()
    
    return render(request, 'cart/detail.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
    })
@login_required
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)
    messages.success(request, f"Added {product.name} to your cart")
    return redirect('cart:cart_detail')
@login_required
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f"Removed {product.name} from your cart")
    return redirect('cart:cart_detail')



# products/views.py
from django.views.generic import ListView
from .models import Product

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category')