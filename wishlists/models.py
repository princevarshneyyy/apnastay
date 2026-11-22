from django.db import models
from django.conf import settings


class Wishlist(models.Model):
    """
    Saves a guest's favourite properties.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlists'
    )
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'listing')

    def __str__(self):
        return f"{self.user.username} saved {self.listing.title}"
