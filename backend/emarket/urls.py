"""
URL configuration for emarket project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenRefreshView, TokenViewBase


class LoginThrottle(AnonRateThrottle):
    scope = 'auth'


class LoginView(TokenViewBase):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    serializer_class = TokenObtainPairSerializer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/',include('product.urls')),
    path('api/',include('account.urls')),
    path('api/token/',LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/',TokenRefreshView.as_view(permission_classes=[AllowAny]), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/',include('order.urls')),
    
]



handler404='utils.error_view.handler404'
handler500='utils.error_view.handler500'
