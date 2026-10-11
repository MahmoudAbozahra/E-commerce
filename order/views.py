from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from product.models import Products

from .models import Cart, CartItem, Order, OrderStatus
from .serializers import (
    CartItemInputSerializer,
    CartSerializer,
    CheckoutAddressSerializer,
    OrderDetailResponseSerializer,
    OrderListSerializer,
    OrderSerializer,
    OrderStatusInputSerializer,
)
from .services import checkout, transition_order

# Create your views here.



@extend_schema(responses={200: OrderListSerializer})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_orders(request):
    order = Order.objects.select_related('user').prefetch_related('orderitems')
    if not request.user.is_staff:
        order = order.filter(user=request.user)
    serializer =OrderSerializer(order,many=True)
    return Response({'orders' : serializer.data})
    
@extend_schema(responses={200: OrderDetailResponseSerializer})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order(request,id):
    order = get_object_or_404(Order.objects.prefetch_related('orderitems'), id=id)
    if not request.user.is_staff and order.user_id != request.user.id:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer =OrderSerializer(order,many=False)
    return Response({'order' : serializer.data})





@extend_schema(request=CheckoutAddressSerializer, responses={201: OrderSerializer})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_order(request):
    serializer = CheckoutAddressSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        order = checkout(user=request.user, address=serializer.validated_data)
    except ValidationError as exc:
        return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
    
    
    
@extend_schema(request=OrderStatusInputSerializer, responses={200: OrderDetailResponseSerializer})
@api_view(['PUT'])
@permission_classes([IsAuthenticated,IsAdminUser])
def process_order(request,id):
    status_serializer = OrderStatusInputSerializer(data=request.data)
    status_serializer.is_valid(raise_exception=True)
    order = get_object_or_404(Order.objects.prefetch_related('orderitems__product'),id=id)
    try:
        order = transition_order(order=order, new_status=status_serializer.validated_data['status'])
    except ValidationError as exc:
        return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
    serializer =OrderSerializer(order,many=False)
    return Response({'order' : serializer.data})
    
    
    
@extend_schema(responses={204: None})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_order(request,id):
    order = get_object_or_404(Order, id=id)
    if not request.user.is_staff and order.user_id != request.user.id:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    if order.status != OrderStatus.CANCELLED:
        try:
            transition_order(order=order, new_status=OrderStatus.CANCELLED)
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(responses=CartSerializer),
    post=extend_schema(request=CartItemInputSerializer, responses={201: CartSerializer}),
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    if request.method == 'GET':
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart = Cart.objects.prefetch_related('items__product').get(pk=cart.pk)
        return Response(CartSerializer(cart).data)
    serializer = CartItemInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart = Cart.objects.select_for_update().get(pk=cart.pk)
            product = Products.objects.select_for_update().get(pk=serializer.validated_data['product_id'])
            item = CartItem.objects.select_for_update().filter(cart=cart, product=product).first()
            requested_quantity = serializer.validated_data['quantity'] + (item.quantity if item else 0)
            if requested_quantity > product.stock:
                raise ValidationError({'quantity': ['Requested quantity exceeds available stock.']})
            if item:
                item.quantity = requested_quantity
                item.save(update_fields=['quantity'])
            else:
                CartItem.objects.create(cart=cart, product=product, quantity=requested_quantity)
            cart = Cart.objects.prefetch_related('items__product').get(pk=cart.pk)
            response_data = CartSerializer(cart).data
    except ValidationError as exc:
        return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
    return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    put=extend_schema(request=CartItemInputSerializer, responses=CartSerializer),
    delete=extend_schema(responses={204: None}),
)
@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_item_detail(request, item_id):
    with transaction.atomic():
        item_ref = get_object_or_404(
            CartItem.objects.filter(cart__user=request.user).only('cart_id'), pk=item_id
        )
        cart_id = item_ref.cart_id
        Cart.objects.select_for_update().get(pk=cart_id)
        item = get_object_or_404(
            CartItem.objects.select_for_update().select_related('product'),
            pk=item_id,
            cart_id=cart_id,
        )
        if request.method == 'DELETE':
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = CartItemInputSerializer(data={'product_id': item.product_id, 'quantity': request.data.get('quantity')})
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data['quantity'] > item.product.stock:
            return Response({'quantity': ['Requested quantity exceeds available stock.']}, status=status.HTTP_400_BAD_REQUEST)
        item.quantity = serializer.validated_data['quantity']
        item.save(update_fields=['quantity'])
        cart = Cart.objects.prefetch_related('items__product').get(pk=item.cart_id)
        return Response(CartSerializer(cart).data)
