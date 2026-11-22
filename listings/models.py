from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Avg, Count
import uuid


class Amenity(models.Model):
    """
    Property amenities like Wi-Fi, Pool, Kitchen, AC, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=60,
        default='bi-check-circle',
        help_text="Bootstrap icon class, e.g. bi-wifi, bi-water, bi-tv"
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = "Amenities"
        ordering = ['name']

    def __str__(self):
        return self.name


class Listing(models.Model):
    """
    Property listing managed by a Host.
    """
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('farmhouse', 'Farmhouse'),
        ('cottage', 'Cottage'),
        ('homestay', 'Homestay'),
        ('resort', 'Resort'),
        ('cabin', 'Cabin'),
        ('unique', 'Unique Stay'),
    ]

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings'
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField()
    property_type = models.CharField(max_length=30, choices=PROPERTY_TYPES, default='apartment', db_index=True)

    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, default='India')

    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per night in INR")
    cleaning_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, blank=True)
    service_fee_percent = models.DecimalField(max_digits=4, decimal_places=2, default=5.00, help_text="Platform fee percentage")

    max_guests = models.PositiveIntegerField(default=1)
    bedrooms = models.PositiveIntegerField(default=1)
    beds = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)

    amenities = models.ManyToManyField(Amenity, blank=True, related_name='listings')

    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city', 'property_type', 'is_active']),
            models.Index(fields=['price_per_night']),
        ]

    def __str__(self):
        return f"{self.title} - {self.city}, {self.state}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'property'
            unique_slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
            self.slug = unique_slug
        super().save(*args, **kwargs)

    @property
    def cover_image(self):
        cover = self.images.filter(is_cover=True).first()
        if not cover:
            cover = self.images.first()
        return cover

    @property
    def average_rating(self):
        result = self.reviews.aggregate(avg=Avg('rating'))
        if result['avg'] is not None:
            return round(float(result['avg']), 1)
        return 0.0

    @property
    def review_count(self):
        return self.reviews.count()

    def calculate_price_breakdown(self, nights):
        """Calculates subtotal, service fee, cleaning fee, and grand total."""
        nights = max(1, int(nights))
        subtotal = self.price_per_night * nights
        service_fee = round((subtotal * self.service_fee_percent) / 100, 2)
        total = subtotal + service_fee + self.cleaning_fee
        return {
            'nights': nights,
            'price_per_night': self.price_per_night,
            'subtotal': subtotal,
            'cleaning_fee': self.cleaning_fee,
            'service_fee': service_fee,
            'total_amount': total,
        }


class ListingImage(models.Model):
    """
    Multiple images for a listing.
    """
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='listings/%Y/%m/')
    is_cover = models.BooleanField(default=False)
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_cover', 'id']

    def __str__(self):
        return f"Image for {self.listing.title} ({'Cover' if self.is_cover else 'Gallery'})"
