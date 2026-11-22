from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Review(models.Model):
    """
    Guest review and star rating (1-5) for a verified completed stay.
    """
    RATING_CHOICES = [
        (1, '1 - Terrible'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]

    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='review',
        help_text="Each completed booking allows exactly one review."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        default=5
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s {self.rating}-star review for {self.listing.title}"

    def clean(self):
        super().clean()
        if self.booking_id and self.listing_id:
            # Booking must belong to this listing
            if self.booking.listing_id != self.listing_id:
                raise ValidationError("This booking does not belong to this listing.")

            # Booking guest must match reviewer
            if self.booking.guest_id != self.user_id:
                raise ValidationError("You can only review bookings made by your account.")

            # Host cannot review their own property
            if self.user_id == self.listing.host_id:
                raise ValidationError("Property hosts cannot review their own properties.")

            # Check eligibility: stay must be completed or confirmed with past check_out date
            today = timezone.now().date()
            is_completed = (self.booking.status == 'completed') or (
                self.booking.status == 'confirmed' and self.booking.check_out <= today
            )
            if not is_completed:
                raise ValidationError("You can only review a property after your stay is completed.")
