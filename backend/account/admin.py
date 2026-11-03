from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, AuditLog, Notification, Profile, User

admin.site.register((Profile, Address, Notification, AuditLog))
admin.site.register(User, UserAdmin)
