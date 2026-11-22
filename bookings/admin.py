from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_id', 'listing', 'guest', 'check_in', 'check_out',
        'total_nights', 'total_amount', 'status', 'payment_status', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at', 'check_in']
    search_fields = [
        'booking_id', 'listing__title', 'guest__username', 'guest__email',
        'listing__city'
    ]
    readonly_fields = [
        'booking_id', 'subtotal', 'service_fee', 'cleaning_fee',
        'total_amount', 'created_at', 'updated_at'
    ]
