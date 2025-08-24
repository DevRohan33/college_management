from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Sum
from django.contrib import messages

from .models import Product, Category, ProductImage, ProductReview, CartItem, Order, SellerProfile

@login_required
def shop_home(request):
    q = request.GET.get('q', '')
    cat = request.GET.get('category')
    minp = request.GET.get('min')
    maxp = request.GET.get('max')

    items = Product.objects.all().select_related('seller', 'category')
    if q:
        items = items.filter(title__icontains=q)
    if cat:
        items = items.filter(category_id=cat)
    if minp:
        items = items.filter(price__gte=minp)
    if maxp:
        items = items.filter(price__lte=maxp)

    items = sorted(items, key=lambda p: p.average_rating(), reverse=True)
    categories = Category.objects.order_by('name')

    return render(request, 'shop/home.html', {
        'items': items,
        'categories': categories,
        'q': q,
        'cat': cat,
        'min': minp,
        'max': maxp,
    })

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    seller_profile, _ = SellerProfile.objects.get_or_create(user=product.seller)
    reviews = product.reviews.select_related('reviewer').order_by('-created_at')
    recommended = Product.objects.exclude(id=product.id)
    recommended = sorted(recommended, key=lambda p: p.average_rating(), reverse=True)[:6]

    if request.method == 'POST' and 'add_cart' in request.POST:
        CartItem.objects.get_or_create(user=request.user, product=product)
        messages.success(request, 'Added to cart.')
        return redirect('shop_cart')
    if request.method == 'POST' and 'buy_now' in request.POST:
        return redirect('shop_buy_now', pk=product.id)

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'seller_profile': seller_profile,
        'reviews': reviews,
        'recommended': recommended,
    })

@login_required
def cart_view(request):
    items = CartItem.objects.filter(user=request.user).select_related('product')
    return render(request, 'shop/cart.html', {'items': items})

@login_required
def cart_delete(request, item_id):
    ci = get_object_or_404(CartItem, id=item_id, user=request.user)
    ci.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('shop_cart')

@login_required
def buy_now(request, pk):
    product = get_object_or_404(Product, pk=pk)
    seller_profile, _ = SellerProfile.objects.get_or_create(user=product.seller)
    if request.method == 'POST':
        method = request.POST.get('payment_method')
        txid = request.POST.get('transaction_id')
        payer = request.POST.get('payment_person_name')
        screenshot = request.FILES.get('payment_screenshot')

        order = Order.objects.create(
            buyer=request.user,
            product=product,
            quantity=1,
            amount=product.price,
            payment_method=method,
            transaction_id=txid,
            payment_person_name=payer,
            payment_screenshot=screenshot,
        )
        messages.success(request, 'Order placed! Seller will verify payment.')
        return redirect('shop_my_orders')

    return render(request, 'shop/buy_now.html', {
        'product': product,
        'seller_profile': seller_profile,
    })

@login_required
def my_orders(request):
    orders = Order.objects.filter(buyer=request.user).select_related('product', 'product__seller')
    # mark whether a review exists for each order's product by this user
    reviewed_ids = set(ProductReview.objects.filter(product_id__in=[o.product_id for o in orders], reviewer=request.user).values_list('product_id', flat=True))
    return render(request, 'shop/my_orders.html', {'orders': orders, 'reviewed_ids': reviewed_ids})

@login_required
def order_add_review(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    if order.status != 'DELIVERED':
        messages.error(request, 'You can review only after delivery.')
        return redirect('shop_my_orders')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            rating = None
        if not rating or rating < 1 or rating > 5:
            messages.error(request, 'Please provide a rating between 1 and 5.')
            return redirect('shop_order_add_review', order_id=order_id)

        # create or update user's review for this product
        pr, created = ProductReview.objects.update_or_create(
            product=order.product,
            reviewer=request.user,
            defaults={'rating': rating, 'comment': comment or ''}
        )
        messages.success(request, 'Review submitted.')
        return redirect('shop_my_orders')

    return render(request, 'shop/add_review.html', {'order': order})

# Seller area
@login_required
def my_shop(request):
    prof, _ = SellerProfile.objects.get_or_create(user=request.user)

    # Handle save/update of payment details
    if request.method == 'POST':
        upi = request.POST.get('upi_id', '').strip()
        qr = request.FILES.get('qr_code')
        prof.upi_id = upi
        if qr:
            prof.qr_code = qr
        prof.save()
        messages.success(request, 'Payment details saved successfully.')
        return redirect('shop_my_shop')

    edit_mode = request.GET.get('edit') == '1'

    products = Product.objects.filter(seller=request.user)
    total_orders = Order.objects.filter(product__seller=request.user).count()
    total_amount = Order.objects.filter(product__seller=request.user, status='DELIVERED').aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'shop/my_shop.html', {
        'profile': prof,
        'products': products,
        'total_products': products.count(),
        'total_orders': total_orders,
        'total_amount': total_amount,
        'edit_mode': edit_mode,
    })

@login_required
def add_product(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        desc = request.POST.get('description')
        price = request.POST.get('price')
        cat_id = request.POST.get('category')
        default_image = request.FILES.get('default_image')
        images = request.FILES.getlist('images')

        p = Product.objects.create(
            seller=request.user,
            title=title,
            description=desc,
            price=price,
            category_id=cat_id or None,
            default_image=default_image,
        )
        for img in images:
            ProductImage.objects.create(product=p, image=img)
        messages.success(request, 'Product added.')
        return redirect('shop_my_shop')

    categories = Category.objects.all()
    return render(request, 'shop/add_product.html', {'categories': categories})

@login_required
def product_manage(request, pk):
    # Fetch without enforcing seller in ORM to allow graceful redirect instead of 404
    product = get_object_or_404(Product, pk=pk)
    if product.seller_id != request.user.id:
        messages.error(request, 'You are not authorized to manage this product.')
        return redirect('shop_my_shop')

    orders = Order.objects.filter(product=product).select_related('buyer')

    if request.method == 'POST':
        # Update order statuses and delivery date
        for o in orders:
            status = request.POST.get(f'status_{o.id}')
            date = request.POST.get(f'delivery_{o.id}')
            if status:
                o.status = status
            if date:
                o.delivery_date = date
            o.save()
        messages.success(request, 'Orders updated.')
        return redirect('shop_product_manage', pk=pk)

    return render(request, 'shop/product_manage.html', {
        'product': product,
        'orders': orders,
    })

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == 'POST':
        # Optionally prevent delete if there are existing orders
        has_orders = Order.objects.filter(product=product).exists()
        if has_orders:
            messages.error(request, 'Cannot delete a product that has orders.')
            return redirect('shop_my_shop')
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('shop_my_shop')
    # If GET, do not allow deletion directly
    messages.error(request, 'Invalid request method.')
    return redirect('shop_my_shop')

@login_required
def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id, product__seller=request.user)
    order.status = 'CANCELLED'
    order.save(update_fields=['status'])
    messages.success(request, 'Order cancelled.')
    return redirect('shop_product_manage', pk=order.product_id)
