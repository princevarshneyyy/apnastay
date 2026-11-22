from django.contrib import admin
from .models import Wishlist


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'listing', 'created_at']
    search_fields = ['user__username', 'listing__title']
