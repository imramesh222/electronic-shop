# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cart.cart import Cart  # This should be the session-based cart
from .models import Order, OrderItem

@login_required
def checkout(request):
    cart = Cart(request)  # This should be the session-based cart
    cart_items = cart.get_cart_items()
    
    if not cart_items:
        messages.warning(request, "Your cart is empty")
        return redirect('cart:cart_detail')
    
    cart_total = cart.get_total_price()
    
    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address', '').strip()
        
        if not shipping_address:
            messages.error(request, "Please provide a shipping address")
            return redirect('orders:checkout')
        
        try:
            # Create order
            order = Order.objects.create(
                user=request.user,
                status='processing',
                is_paid=True,
                total_price=cart_total,
                shipping_address=shipping_address
            )
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['price']
                )
            
            # Clear the cart
            cart.clear()
            
            messages.success(request, "Your order has been placed successfully!")
            return redirect('orders:order_detail', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('orders:checkout')
    
    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'cart_total': cart_total
    })

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})