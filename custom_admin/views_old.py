from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from orders.models import Order, OrderItem
from products.models import Product, Category
from django.core.paginator import Paginator
from django import forms
from django.forms import ModelForm
import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'slug', 'category', 'description', 'price', 'stock', 'available', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
        }

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('custom_admin:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('custom_admin:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
    
    return render(request, 'custom_admin/login.html')

@login_required(login_url='custom_admin:login')
def admin_logout(request):
    logout(request)
    return redirect('custom_admin:login')

@login_required(login_url='custom_admin:login')
def dashboard(request):
    if not request.user.is_staff:
        return redirect('custom_admin:login')
    
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
    
    # Top selling products
    top_products = OrderItem.objects.values('product__name', 'product__id').annotate(
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
    
    # Monthly revenue trend (last 6 months)
    monthly_trend = []
    for i in range(6):
        month_start = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_start = timezone.make_aware(datetime.combine(month_start, datetime.min.time()))
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        month_end = timezone.make_aware(datetime.combine(month_end, datetime.max.time().replace(microsecond=0)))
        
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
    
    monthly_trend.reverse()
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    
    # Recent pending orders
    pending_orders_list = Order.objects.select_related('user').filter(status='pending').order_by('-created_at')[:5]
    
    context = {
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
        'top_products': top_products,
        'category_performance': category_performance,
        'order_status_counts': order_status_counts,
        'monthly_trend': json.dumps(monthly_trend),
        'revenue_growth': calculate_growth(this_month_revenue, last_month_revenue),
        'order_growth': calculate_growth(this_month_orders, last_month_orders),
        'recent_orders': recent_orders,
        'pending_orders_list': pending_orders_list,
    }
    
    return render(request, 'custom_admin/dashboard.html', context)

@login_required(login_url='custom_admin:login')
def orders_list(request):
    if not request.user.is_staff:
        return redirect('custom_admin:login')
    
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment', '')
    search_query = request.GET.get('search', '')
    
    orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if payment_filter:
        if payment_filter == 'paid':
            orders = orders.filter(is_paid=True)
        elif payment_filter == 'unpaid':
            orders = orders.filter(is_paid=False)
    
    if search_query:
        orders = orders.filter(
            Q(user__email__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(shipping_address__icontains=search_query)
        )
    
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'search_query': search_query,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'custom_admin/orders.html', context)

@login_required(login_url='custom_admin:login')
def order_detail(request, order_id):
    if not request.user.is_staff:
        return redirect('custom_admin:login')
    
    order = get_object_or_404(Order.objects.select_related('user').prefetch_related('items__product'), id=order_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            order.status = 'processing'
            order.updated_at = timezone.now()
            order.save()
            messages.success(request, f'Order {order.id} has been accepted and marked as processing.')
        elif action == 'reject':
            order.status = 'cancelled'
            order.updated_at = timezone.now()
            order.save()
            messages.success(request, f'Order {order.id} has been rejected and marked as cancelled.')
        elif action == 'mark_paid':
            order.is_paid = True
            order.updated_at = timezone.now()
            order.save()
            messages.success(request, f'Order {order.id} has been marked as paid.')
        elif action == 'mark_unpaid':
            order.is_paid = False
            order.updated_at = timezone.now()
            order.save()
            messages.success(request, f'Order {order.id} has been marked as unpaid.')
        elif action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.updated_at = timezone.now()
                order.save()
                messages.success(request, f'Order {order.id} status updated to {new_status}.')
        
        return redirect('custom_admin:order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'custom_admin/order_detail.html', context)

@login_required(login_url='custom_admin:login')
def products_list(request):
    if not request.user.is_staff:
        return redirect('custom_admin:login')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully!')
            return redirect('custom_admin:products')
    else:
        form = ProductForm()
    
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    
    products = Product.objects.select_related('category').order_by('-created_at')
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'category_filter': category_filter,
        'search_query': search_query,
        'categories': categories,
        'form': form,
    }
    
    return render(request, 'custom_admin/products.html', context)

@login_required(login_url='custom_admin:login')
def edit_product(request, product_id):
    if not request.user.is_staff:
        return redirect('custom_admin:login')
    
    product = get_object_or_404(Product.objects.select_related('category'), id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('custom_admin:products')
    else:
        form = ProductForm(instance=product)
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'product': product,
        'categories': categories,
        'edit_mode': True,
    }
    
    return render(request, 'custom_admin/product_form.html', context)

@login_required(login_url='custom_admin:login')
def delete_product(request, product_id):
    if not request.user.is_staff:
        return redirect('custom_admin:login')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        if product.image:
            product.image.delete()
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('custom_admin:products')
    
    context = {
        'product': product,
    }
    
    return render(request, 'custom_admin/product_delete.html', context)

def calculate_growth(current, previous):
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 2)

@login_required(login_url='custom_admin:login')
def categories_list(request):
    if not request.user.is_staff:
        return redirect('custom_admin:login')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('custom_admin:categories')
    else:
        form = CategoryForm()
    
    categories = Category.objects.annotate(product_count=Count('products')).order_by('name')
    
    context = {
        'categories': categories,
        'form': form,
    }
    
    return render(request, 'custom_admin/categories.html', context)

@login_required(login_url='custom_admin:login')
def edit_category(request, category_id):
    if not request.user.is_staff:
        return redirect('custom_admin:login')
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('custom_admin:categories')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'edit_mode': True,
    }
    
    return render(request, 'custom_admin/category_form.html', context)

@login_required(login_url='custom_admin:login')
def delete_category(request, category_id):
    if not request.user.is_staff:
        return redirect('custom_admin:login')
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('custom_admin:categories')
    
    context = {
        'category': category,
    }
    
    return render(request, 'custom_admin/category_delete.html', context)

def calculate_growth(current, previous):
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 2)
