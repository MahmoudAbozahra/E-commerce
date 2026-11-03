import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Address, AuditLog, Notification, Profile
from .serializers import (
    AddressSerializer,
    AuditLogSerializer,
    ChangePasswordSerializer,
    NotificationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class AuthThrottle(AnonRateThrottle):
    scope = "auth"


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    throttle_classes = (AuthThrottle,)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=ChangePasswordSerializer, responses={204: None})
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=("password",))
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {"refresh": {"type": "string"}}, "required": ["refresh"]}}, responses={204: None}
    )
    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"refresh": ["This field is required."]}, status=400)
        RefreshToken(token).blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (AuthThrottle,)

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: None})
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()
        if user:
            token = secrets.token_urlsafe(32)
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.reset_token_digest = hashlib.sha256(token.encode()).hexdigest()
            profile.reset_password_expire = timezone.now() + timedelta(minutes=30)
            profile.save(update_fields=("reset_token_digest", "reset_password_expire"))
            send_mail("Password reset", f"Use this one-time token within 30 minutes: {token}", None, [user.email], fail_silently=True)
        return Response({"detail": "If an account exists, reset instructions have been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (AuthThrottle,)

    @extend_schema(request=PasswordResetConfirmSerializer, responses={204: None})
    @transaction.atomic
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        digest = hashlib.sha256(serializer.validated_data["token"].encode()).hexdigest()
        profile = Profile.objects.select_for_update().filter(reset_token_digest=digest, reset_password_expire__gt=timezone.now()).select_related("user").first()
        if not profile:
            return Response({"token": ["Invalid or expired token."]}, status=400)
        profile.user.set_password(serializer.validated_data["password"])
        profile.user.save(update_fields=("password",))
        profile.reset_token_digest = ""
        profile.reset_password_expire = None
        profile.save(update_fields=("reset_token_digest", "reset_password_expire"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        was_default = instance.is_default
        user = instance.user
        instance.delete()
        if was_default:
            replacement = user.addresses.order_by("id").first()
            if replacement:
                replacement.is_default = True
                replacement.save(update_fields=("is_default",))


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=("post",))
    def read(self, request, pk=None):
        notification = self.get_object()
        if not notification.read_at:
            notification.read_at = timezone.now()
            notification.save(update_fields=("read_at",))
        return Response(self.get_serializer(notification).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("actor")
