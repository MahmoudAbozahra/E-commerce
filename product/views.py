from django.shortcuts import get_object_or_404, render 
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from .models import Products
from .serializers import productserializer
from .filters import ProductsFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated 
from rest_framework import status
# Create your views here.


@api_view(['GET'])
def get_all_products(request):
    #products = Products.objects.all()
    filterset= ProductsFilter(request.GET,queryset=Products.objects.all().order_by('id'))
    #serializer = productserializer(products,many=True)
    count = filterset.qs.count()
    serializer = productserializer(filterset.qs,many=True)
    page = 2
    Paginator =PageNumberPagination()
    Paginator.page_size = page
    queryset= Paginator.paginate_queryset(filterset.qs,request)
    serializer = productserializer(queryset,many=True)
    return Response({'products':serializer.data ,'per page':page , 'count':count} )



@api_view(['GET'])
def get_by_id_product(request , g_id):
    products = get_object_or_404(Products,id=g_id)
    serializer = productserializer(products,many=False)
    return Response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_product(request):
    data = request.data 
    serializer = productserializer(data=data)
    
    if serializer.is_valid():
        product = Products.objects.create(**data,user=request.user)
        res = productserializer(product,many=False)
        
        
        
        return Response({"product":res.data})
    else:
        return Response(serializer.errors)
    
    #     serializer.save(user=request.user)
    #     return Response(serializer.data , status=status.HTTP_201_CREATED)
    # return Response(serializer.data , status=status.HTTP_400_BAD_REQUEST)
    
    
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])    
def product_update(request , id):
    product = get_object_or_404(Products,id=id)
     
    if product.user != request.user :
        return Response({"error":"sorry you can not update this product"},status=status.HTTP_403_FORBIDDEN)
    else:
        product.name = request.data['name']
        product.description = request.data['description']
        product.price = request.data['price']
        product.brand = request.data['brand']
        product.category = request.data['category']
        product.rating = request.data['rating']
        product.stock = request.data['stock']
        
        product.save()
        serializer = productserializer(product,many=False)
        return Response({"product":serializer.data})
    
    
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])    
def product_delete(request , id):
    product = get_object_or_404(Products,id=id)
     
    if product.user != request.user :
        return Response({"error":"sorry you can not update this delete"},status=status.HTTP_403_FORBIDDEN)
    
    product.delete()
    return Response({"details":"Delete action done"},status=status.HTTP_200_OK)