from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop_home, name='shop_home'),
    path('product/<int:pk>/', views.product_detail, name='shop_product_detail'),
    path('cart/', views.cart_view, name='shop_cart'),
    path('buy/<int:pk>/', views.buy_now, name='shop_buy_now'),
    path('orders/', views.my_orders, name='shop_my_orders'),
    path('orders/<int:order_id>/review/', views.order_add_review, name='shop_order_add_review'),
    path('my/', views.my_shop, name='shop_my_shop'),
    path('my/add/', views.add_product, name='shop_add_product'),
    path('my/product/<int:pk>/', views.product_manage, name='shop_product_manage'),
    path('my/product/<int:pk>/delete/', views.product_delete, name='shop_product_delete'),
    path('my/order/<int:order_id>/cancel/', views.order_cancel, name='shop_order_cancel'),
    path('cart/delete/<int:item_id>/', views.cart_delete, name='shop_cart_delete'),
]
