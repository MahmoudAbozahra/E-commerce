from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import Profile
from .serializers import PasswordResetConfirmSerializer, PasswordResetRequestSerializer, ProfileUpdateSerializer, SignUpSerializer, UserSerializer


class SensitiveEndpointThrottle(AnonRateThrottle):
    scope = 'auth'

# Create your views here.

@extend_schema(request=SignUpSerializer, responses={201: UserSerializer})
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([SensitiveEndpointThrottle])
def register(request):
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

@extend_schema(responses={200: UserSerializer})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = UserSerializer(request.user)
    return Response(user.data)


@extend_schema(request=ProfileUpdateSerializer, responses={200: UserSerializer})
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request):
    serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(UserSerializer(request.user).data)



def get_curent_host(request):
    protocol = 'https' if request.is_secure() else 'http'
    return f"{protocol}://{request.get_host()}/"


@extend_schema(request=PasswordResetRequestSerializer, responses={200: None})
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([SensitiveEndpointThrottle])
def forget_password(request):
    request_serializer = PasswordResetRequestSerializer(data=request.data)
    request_serializer.is_valid(raise_exception=True)
    email = request_serializer.validated_data['email']
    for user in User.objects.filter(email__iexact=email, is_active=True):
        token = get_random_string(40)
        user.profile.reset_password_token = token
        user.profile.reset_password_expire = timezone.now() + timedelta(minutes=30)
        user.profile.save(update_fields=['reset_password_token', 'reset_password_expire'])
        link = f"{get_curent_host(request)}api/reset_password/{token}"
        send_mail('Password reset', f'Use this link to reset your password: {link}', None, [user.email], fail_silently=True)
    return Response({'details': 'If an account exists for that email, reset instructions have been sent.'})
    
    
    
@extend_schema(request=PasswordResetConfirmSerializer, responses={200: None})
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([SensitiveEndpointThrottle])
def reset_password(request,token):
    request_serializer = PasswordResetConfirmSerializer(data=request.data)
    request_serializer.is_valid(raise_exception=True)
    data = request_serializer.validated_data
    with transaction.atomic():
        profile = get_object_or_404(Profile.objects.select_for_update().select_related('user'), reset_password_token=token)
        user = profile.user
        if not profile.reset_password_expire or profile.reset_password_expire < timezone.now():
            return Response({'error':'Token is expired'},status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(data.get('password'), user)
        except ValidationError as exc:
            return Response({'password': list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data['password'])
        profile.reset_password_token = ""
        profile.reset_password_expire = None
        profile.save(update_fields=['reset_password_token', 'reset_password_expire'])
        user.save(update_fields=['password'])
    return Response({'details':'password rest done'})
