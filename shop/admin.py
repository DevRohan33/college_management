from .models import Product, Category, CartItem, ProductImage, ProductReview, Order,SellerProfile
from django.contrib import admin   

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(CartItem)
admin.site.register(ProductImage)
admin.site.register(ProductReview)
admin.site.register(Order)
admin.site.register(SellerProfile)