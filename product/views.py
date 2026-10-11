from django.db import transaction
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .filters import ProductsFilter
from .models import Products
from .serializers import ProductPageSerializer, ProductSerializer, ReviewSerializer

# Create your views here.


@extend_schema(operation_id='products_list', responses={200: ProductPageSerializer})
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_products(request):
    #products = Products.objects.all()
    filterset= ProductsFilter(request.GET,queryset=Products.objects.prefetch_related('reviews__user').order_by('id'))
    paginator = PageNumberPagination()
    paginator.page_size = 20
    queryset = paginator.paginate_queryset(filterset.qs, request)
    return paginator.get_paginated_response(ProductSerializer(queryset,many=True).data)



@extend_schema(operation_id='product_retrieve', responses={200: ProductSerializer})
@api_view(['GET'])
@permission_classes([AllowAny])
def get_by_id_product(request , g_id):
    products = get_object_or_404(Products,id=g_id)
    serializer = ProductSerializer(products,many=False)
    return Response(serializer.data)



@extend_schema(request=ProductSerializer, responses={201: ProductSerializer})
@api_view(['POST'])
@permission_classes([IsAuthenticated,IsAdminUser])
def new_product(request):
    serializer = ProductSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    product = serializer.save(user=request.user)
    return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
    
    #     serializer.save(user=request.user)
    #     return Response(serializer.data , status=status.HTTP_201_CREATED)
    # return Response(serializer.data , status=status.HTTP_400_BAD_REQUEST)
    
    
    
@extend_schema(request=ProductSerializer, responses=ProductSerializer)
@api_view(['PUT'])
@permission_classes([IsAuthenticated,IsAdminUser])    
def product_update(request , id):
    product = get_object_or_404(Products,id=id)
    if not request.user.is_staff:
        return Response({"detail": "Administrator access required."}, status=status.HTTP_403_FORBIDDEN)
    serializer = ProductSerializer(product, data=request.data, partial=request.method == 'PATCH')
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
    
    
    
@extend_schema(responses={204: None})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsAdminUser])    
def product_delete(request , id):
    product = get_object_or_404(Products,id=id)
    if not request.user.is_staff:
        return Response({"detail": "Administrator access required."}, status=status.HTTP_403_FORBIDDEN)
    product.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)



@extend_schema(request=ReviewSerializer, responses={200: ReviewSerializer, 201: ReviewSerializer})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review(request,id):
    serializer = ReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        product = get_object_or_404(Products.objects.select_for_update(), id=id)
        review_obj = product.reviews.filter(user=request.user).first()
        if review_obj:
            serializer = ReviewSerializer(review_obj, data=request.data)
            serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, product=product)
        product.rating = product.reviews.aggregate(value=Avg('rating'))['value'] or 0
        product.save(update_fields=['rating'])
    return Response(serializer.data, status=status.HTTP_200_OK if review_obj else status.HTTP_201_CREATED)
    
    
    
    
@extend_schema(responses={204: None})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_review(request,id):
    with transaction.atomic():
        product = get_object_or_404(Products.objects.select_for_update(), id=id)
        deleted, _ = product.reviews.filter(user=request.user).delete()
        if not deleted:
            return Response({'error':'Review not found'},status=status.HTTP_404_NOT_FOUND)
        product.rating = product.reviews.aggregate(value=Avg('rating'))['value'] or 0
        product.save(update_fields=['rating'])
    return Response(status=status.HTTP_204_NO_CONTENT)
            
