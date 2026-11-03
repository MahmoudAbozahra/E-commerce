from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    AddressViewSet,
    AuditLogViewSet,
    ChangePasswordView,
    LogoutView,
    MeView,
    NotificationViewSet,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
)

router = DefaultRouter()
router.register("users/addresses", AddressViewSet, basename="address")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("admin/audit-logs", AuditLogViewSet, basename="admin-audit-log")

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", TokenObtainPairView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/password/change/", ChangePasswordView.as_view()),
    path("auth/password/reset/request/", PasswordResetRequestView.as_view()),
    path("auth/password/reset/confirm/", PasswordResetConfirmView.as_view()),
    path("users/me/", MeView.as_view()),
    path("", include(router.urls)),
]
