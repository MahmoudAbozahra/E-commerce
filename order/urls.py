from django.urls import path
from . import views



urlpatterns = [
    path('orders/new/',views.new_order,name='new_order'),
    path('orders/',views.get_orders,name='get_orders'),
    path('order/<str:id>/',views.get_order,name='get_order'),
    path('order/<str:id>/process/',views.process_order,name='process_order'),
    path('order/<str:id>/delete/',views.delete_order,name='delete_order'),
]
