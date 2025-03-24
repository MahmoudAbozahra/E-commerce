from django.urls import path
from . import views



urlpatterns = [
    path('products/',views.get_all_products,name='products'),
    path('products/<str:g_id>/',views.get_by_id_product,name='get_by_id_product'),
    path('new_product/',views.new_product,name='new_product'),
    path('products/update/<str:id>/',views.product_update,name='update'),
    path('products/delete/<str:id>/',views.product_delete,name='delete'),
    path('<str:id>/review/',views.review,name='review'),
    path('<str:id>/review/delete/',views.delete_review,name='delete_review'),
]
