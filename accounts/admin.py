from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom Admin for ApnaStay User model.
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_host', 'is_staff', 'date_joined']
    list_filter = ['is_host', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('ApnaStay Profile', {
            'fields': ('phone_number', 'profile_picture', 'bio', 'is_host'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('ApnaStay Profile', {
            'fields': ('email', 'phone_number', 'is_host'),
        }),
    )
    search_fields = ['username', 'email', 'first_name', 'last_name']
