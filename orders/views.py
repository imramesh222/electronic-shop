# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cart.cart import Cart  # This should be the session-based cart
from .models import Order, OrderItem
from django.views.generic import DetailView
from core.mixins import LoginRequiredToBuyMixin

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



class OrderDetailView(LoginRequiredToBuyMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    login_url = 'accounts:login'

    def get_object(self):
        return get_object_or_404(Order, pk=self.kwargs.get('pk'), user=self.request.user)

class OrderInvoiceView(LoginRequiredToBuyMixin, DetailView):
    model = Order
    template_name = 'orders/invoice.html'
    context_object_name = 'order'
    login_url = 'accounts:login'

    def get_object(self):
        return get_object_or_404(Order, pk=self.kwargs.get('pk'), user=self.request.user)

class OrderCancel(LoginRequiredToBuyMixin, DetailView):
    model = Order
    template_name = 'orders/order_cancel.html'
    context_object_name = 'order'
    login_url = 'accounts:login'

    def get_object(self):
        order = get_object_or_404(Order, pk=self.kwargs.get('order_id'), user=self.request.user)
        if order.status != 'processing':
            messages.error(self.request, "Only processing orders can be canceled.")
            return redirect('orders:order_detail', pk=order.pk)
        order.status = 'canceled'
        order.save()
        messages.success(self.request, "Your order has been canceled.")
        return order

class OrderReturn(LoginRequiredToBuyMixin, DetailView):
    model = Order
    template_name = 'orders/order_return.html'
    context_object_name = 'order'
    login_url = 'accounts:login'

    def get_object(self):
        order = get_object_or_404(Order, pk=self.kwargs.get('order_id'), user=self.request.user)
        if order.status != 'delivered':
            messages.error(self.request, "Only delivered orders can be returned.")
            return redirect('orders:order_detail', pk=order.pk)
        order.status = 'returned'
        order.save()
        messages.success(self.request, "Your return request has been processed.")
        return order