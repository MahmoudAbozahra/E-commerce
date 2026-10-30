from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Cart, CartItem, Order, OrderItem, OrderStatus


class OrderItemSerializer(serializers.ModelSerializer):
   class Meta:
        model = OrderItem
        fields = "__all__"
       
       
       
class OrderSerializer(serializers.ModelSerializer):
    orderItems=serializers.SerializerMethodField(method_name="get_order_items",read_only=True)
    class Meta:
        model = Order
        fields = (
            'id', 'city', 'zip_code', 'street', 'state', 'country', 'phone_no',
            'total_amount', 'payment_status', 'payment_method', 'status', 'user',
            'createAt', 'orderItems',
        )
        read_only_fields = ('id', 'total_amount', 'payment_status', 'status', 'user', 'createAt')
        
        
        
    @extend_schema_field(OrderItemSerializer(many=True))
    def get_order_items(self,obj):
        order_items = obj.orderitems.all()
        serializer = OrderItemSerializer(order_items,many=True)
        return serializer.data


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    name = serializers.CharField(source='product.name', read_only=True)
    price = serializers.DecimalField(source='product.price', max_digits=9, decimal_places=2, read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ('id', 'product_id', 'name', 'price', 'quantity', 'line_total')

    @extend_schema_field(serializers.DecimalField(max_digits=19, decimal_places=2))
    def get_line_total(self, item):
        return item.product.price * item.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('items', 'total')

    @extend_schema_field(serializers.DecimalField(max_digits=19, decimal_places=2))
    def get_total(self, cart):
        return sum((item.product.price * item.quantity for item in cart.items.all()), start=Decimal('0.00'))


class CartItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        from product.models import Products
        if not Products.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Product does not exist.')
        return value


class CheckoutAddressSerializer(serializers.Serializer):
    city = serializers.CharField(max_length=100)
    zip_code = serializers.CharField(max_length=20)
    street = serializers.CharField(max_length=255)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    country = serializers.CharField(max_length=100)
    phone_no = serializers.CharField(max_length=30)


class OrderListSerializer(serializers.Serializer):
    orders = OrderSerializer(many=True)


class OrderDetailResponseSerializer(serializers.Serializer):
    order = OrderSerializer()


class OrderStatusInputSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices)
