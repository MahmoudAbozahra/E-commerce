import django_filters 

from .models import Products

class ProductsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    minprice = django_filters.filters.NumberFilter(field_name="price" or 0,lookup_expr="gte")
    maxprice = django_filters.filters.NumberFilter(field_name="price" or 10000,lookup_expr="lte")
    brand=django_filters.CharFilter(field_name="brand",lookup_expr="icontains")
    category=django_filters.CharFilter(field_name="category",lookup_expr="icontains")
    class Meta:
        model = Products 
        # fields = ['brand','category']
        fields = ['brand','category','minprice','maxprice']
            