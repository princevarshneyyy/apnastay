from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import datetime


class Booking(models.Model):
    """
    Accommodation booking by a guest for a listing.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    PAYMENT_CHOICES = [
        ('pay_at_property', 'Pay at property'),
        ('paid', 'Paid Online'),
    ]

    booking_id = models.CharField(max_length=32, unique=True, editable=False)
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    guest = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    check_in = models.DateField(db_index=True)
    check_out = models.DateField(db_index=True)
    guests_count = models.PositiveIntegerField(default=1)

    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    total_nights = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed', db_index=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pay_at_property')

    special_requests = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['listing', 'status', 'check_in', 'check_out']),
            models.Index(fields=['guest', 'status']),
        ]

    def __str__(self):
        return f"Booking {self.booking_id} - {self.listing.title} ({self.guest.username})"

    def clean(self):
        super().clean()
        today = timezone.now().date()

        if self.check_in and self.check_out:
            if self.check_out <= self.check_in:
                raise ValidationError({'check_out': 'Check-out date must be strictly after the check-in date.'})

            # For new bookings, check_in must not be in past
            if not self.pk and self.check_in < today:
                raise ValidationError({'check_in': 'Check-in date cannot be in the past.'})

        if self.listing_id:
            listing = self.listing
            if self.guest_id and self.guest_id == listing.host_id:
                raise ValidationError({'guest': 'Property hosts cannot book their own property.'})

            if self.guests_count > listing.max_guests:
                raise ValidationError({
                    'guests_count': f"This property accommodates a maximum of {listing.max_guests} guests."
                })

            # Check overlapping confirmed/pending bookings
            overlapping = Booking.objects.filter(
                listing=listing,
                status__in=['confirmed', 'pending'],
                check_in__lt=self.check_out,
                check_out__gt=self.check_in,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError('The selected dates are already booked. Please choose different dates.')

    def save(self, *args, **kwargs):
        if not self.booking_id:
            now_str = timezone.now().strftime('%Y%m')
            random_code = uuid.uuid4().hex[:6].upper()
            self.booking_id = f"APNA-{now_str}-{random_code}"

        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            self.total_nights = max(1, delta.days)

        if not self.subtotal:
            self.subtotal = self.price_per_night * self.total_nights
        if not self.total_amount:
            self.total_amount = self.subtotal + self.service_fee + self.cleaning_fee

        super().save(*args, **kwargs)

    @property
    def can_cancel(self):
        """Allows guest or host to cancel if check-in is in the future and status is active."""
        today = timezone.now().date()
        return self.status in ['pending', 'confirmed'] and self.check_in >= today

    @property
    def can_review(self):
        """
        Allows guest to submit a review only if the stay is completed
        (or confirmed and check_out is in the past) and no review has been submitted yet.
        """
        today = timezone.now().date()
        is_stay_over = self.status == 'completed' or (self.status == 'confirmed' and self.check_out <= today)
        has_review = hasattr(self, 'review')
        return is_stay_over and not has_review
