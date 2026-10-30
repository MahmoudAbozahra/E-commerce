from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, validators=[validate_password])
    email = serializers.EmailField()
    
    class Meta:
        model = User
        fields = ('first_name','last_name','username','email','password')
        
        extra_kwargs = {
            'first_name':{'required':True,'allow_blank':False},
            'last_name':{'required':True,'allow_blank':False},
            'username':{'required':True,'allow_blank':False},
            'email':{'required':True,'allow_blank':False},
            'password':{'required':True,'allow_blank':False,'min_length':8},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
        
        
class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ('first_name','last_name','username','email')


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')

    def validate_email(self, value):
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=value).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirmPassword = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirmPassword']:
            raise serializers.ValidationError({'confirmPassword': 'Passwords do not match.'})
        return attrs
        

