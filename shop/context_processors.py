from .models import CartItem, Order

def shop_counts(request):
    if not request.user.is_authenticated:
        return {}
    
    cart_count = CartItem.objects.filter(user=request.user).count()
    seller_pending_count = Order.objects.filter(
        product__seller=request.user,
        status='REQUESTED'
    ).count()
    
    total_count = cart_count + seller_pending_count
    
    return {
        'cart_count': cart_count,
        'seller_pending_count': seller_pending_count,
        'shop_total_count': total_count,
    }
