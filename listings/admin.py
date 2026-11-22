from django.contrib import admin
from .models import Amenity, Listing, ListingImage


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ['image', 'is_cover', 'caption']


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'description']
    search_fields = ['name']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'host', 'property_type', 'city', 'state',
        'price_per_night', 'max_guests', 'is_active', 'is_featured', 'created_at'
    ]
    list_filter = ['property_type', 'city', 'state', 'is_active', 'is_featured', 'created_at']
    search_fields = ['title', 'description', 'city', 'state', 'address', 'host__username', 'host__email']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ListingImageInline]
    filter_horizontal = ['amenities']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ['listing', 'is_cover', 'caption', 'created_at']
    list_filter = ['is_cover', 'created_at']
    search_fields = ['listing__title', 'caption']
