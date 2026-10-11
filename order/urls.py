from django.urls import path

from . import views

urlpatterns = [
    path('cart/', views.cart_detail, name='cart'),
    path('cart/items/<int:item_id>/', views.cart_item_detail, name='cart_item'),
    path('orders/new/',views.new_order,name='new_order'),
    path('orders/',views.get_orders,name='get_orders'),
    path('order/<int:id>/',views.get_order,name='get_order'),
    path('order/<int:id>/process/',views.process_order,name='process_order'),
    path('order/<int:id>/delete/',views.delete_order,name='delete_order'),
]
