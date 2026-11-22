from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Review
from .forms import ReviewForm
from listings.models import Listing
from bookings.models import Booking


@login_required
def review_create_view(request, booking_id):
    """
    Submits a review for an eligible completed stay.
    Guarantees that only guests with a completed booking can submit a review.
    """
    booking = get_object_or_404(
        Booking.objects.select_related('listing', 'listing__host'),
        booking_id=booking_id
    )

    if booking.guest != request.user:
        raise PermissionDenied("You can only submit reviews for bookings made by you.")

    if not booking.can_review:
        messages.error(
            request,
            "You cannot review this property yet. A review can only be submitted after your stay is completed."
        )
        return redirect('listings:detail', slug=booking.listing.slug)

    if hasattr(booking, 'review'):
        messages.info(request, "You have already submitted a review for this booking.")
        return redirect('listings:detail', slug=booking.listing.slug)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.listing = booking.listing
            review.booking = booking
            review.user = request.user
            try:
                review.full_clean()
                review.save()
                messages.success(request, "Thank you! Your review and rating have been published.")
                return redirect('listings:detail', slug=booking.listing.slug)
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please check the review form for errors.")
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'booking': booking,
        'listing': booking.listing,
    }
    return render(request, 'reviews/form.html', context)


@login_required
def review_update_view(request, review_id):
    """Allows guest to edit their existing review."""
    review = get_object_or_404(Review.objects.select_related('listing'), id=review_id)

    if review.user != request.user and not request.user.is_staff:
        raise PermissionDenied("You cannot edit someone else's review.")

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Your review has been updated.")
            return redirect('listings:detail', slug=review.listing.slug)
    else:
        form = ReviewForm(instance=review)

    context = {
        'form': form,
        'review': review,
        'listing': review.listing,
        'is_edit': True,
    }
    return render(request, 'reviews/form.html', context)


@login_required
@require_POST
def review_delete_view(request, review_id):
    """Allows guest to delete their review."""
    review = get_object_or_404(Review.objects.select_related('listing'), id=review_id)

    if review.user != request.user and not request.user.is_staff:
        raise PermissionDenied("You cannot delete this review.")

    listing_slug = review.listing.slug
    review.delete()
    messages.info(request, "Your review has been deleted.")
    return redirect('listings:detail', slug=listing_slug)
