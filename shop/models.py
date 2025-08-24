from django.db import models
from django.conf import settings
from account.models import Department, Semester

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Product(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shop_products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    default_image = models.ImageField(upload_to='shop/products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def average_rating(self):
        agg = self.reviews.aggregate(models.Avg('rating'))
        return round(agg['rating__avg'] or 0, 1)

    def seller_avg_rating(self):
        from django.db.models import Avg
        return round(ProductReview.objects.filter(product__seller=self.seller).aggregate(avg=Avg('rating'))['avg'] or 0, 1)

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='shop/products/')

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # 1..5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    PAYMENT_METHODS = (
        ('ONLINE', 'Online'),
        ('COD', 'Cash on Delivery'),
    )
    STATUS_CHOICES = (
        ('REQUESTED', 'Order Request Sent'),
        ('DELIVERY_DAY', 'Delivery Day Assigned'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_person_name = models.CharField(max_length=100, blank=True, null=True)
    payment_screenshot = models.ImageField(upload_to='shop/payments/', blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    delivery_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class SellerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_profile')
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    qr_code = models.ImageField(upload_to='shop/qr/', blank=True, null=True)

    def rating(self):
        from django.db.models import Avg
        return round(ProductReview.objects.filter(product__seller=self.user).aggregate(avg=Avg('rating'))['avg'] or 0, 1)

    def __str__(self):
        return f"SellerProfile({self.user.username})"
