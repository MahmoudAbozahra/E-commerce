from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404, render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework import status
from .serializers import SignUpSerializer ,UserSerializer
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    data = request.data 
    user = SignUpSerializer(data=data)
    
    if user.is_valid():
        if not User.objects.filter(username=data['email']).exists():
            user= User.objects.create(
                first_name=data['first_name'],
                last_name = data['last_name'],
                username = data['username'],
                email =  data['email'],
                password = make_password(data['password']),
            )
            return Response({'details':'Your account registered susccessfully!'},status=status.HTTP_201_CREATED)
        return Response({'details':'this email already exists'},status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(user.errors)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = UserSerializer(request.user)
    return Response(user.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request):
   
    user = request.user
    data = request.data 
    
    user.first_name=data['first_name']
    user.last_name=data['last_name']
    user.username=data['username']
    user.email=data['email']
    
    if data['password'] != '':
        user.password=make_password(data['password'])
        
        
    user.save()
    serializer = UserSerializer(user , many=False)
    return Response(serializer.data)



def get_curent_host(request):
    protocol=request.is_secure() and 'http' or 'https'
    host = request.get_host()
    return "{protocol}://{host}/".format(protocol=protocol,host=host)


@api_view(['POST'])
@permission_classes([AllowAny])
def forget_password(request):
    data = request.data 
    user = get_object_or_404(User,email=data['email'])
    token = get_random_string(40)
    expire_date = datetime.now() + timedelta(minutes=30)
    user.profile.reset_password_token = token
    user.profile.reset_password_expire = expire_date
    user.profile.save()
    host = get_curent_host(request)
    link = f"{host}api/reset_password/{token}"
    body = "Your password reset link is :{link}".format(link=link)
    send_mail(
        "password reset from Emarket",
        body,
        "Emarket@gmail.com",
        [data['email']]
    )
    return Response({'details':'password rest send to {email}'.format(email=data['email'])})
    
    
    
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request,token):
    data = request.data 
    user = get_object_or_404(User,profile__reset_password_token = token)
    
    
    if user.profile.reset_password_expire.replace(tzinfo=None) < datetime.now():
        return Response({'error':'Token is expired'},status=status.HTTP_400_BAD_REQUEST)
    
    if data['password'] != data['confirmPassword']:
        return Response({'error':'Password are not same'},status=status.HTTP_400_BAD_REQUEST)
    
    user.password = make_password(data['password'])
    user.profile.reset_password_token = ""
    user.profile.reset_password_expire = None
    user.profile.save()
    user.save() 
    return Response({'details':'password rest done'})