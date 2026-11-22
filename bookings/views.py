from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from datetime import datetime

from .models import Booking
from .forms import BookingForm
from listings.models import Listing


@login_required
def booking_create_view(request, slug):
    """
    Handles booking submission with atomic locking to prevent race conditions and double bookings.
    """
    listing = get_object_or_404(Listing, slug=slug, is_active=True)

    # Validation: Host cannot book own property
    if listing.host == request.user:
        messages.error(request, "You cannot book your own property listing.")
        return redirect('listings:detail', slug=listing.slug)

    # Pre-populate dates if passed from listing page
    initial_data = {}
    if request.GET.get('check_in'):
        initial_data['check_in'] = request.GET.get('check_in')
    if request.GET.get('check_out'):
        initial_data['check_out'] = request.GET.get('check_out')
    if request.GET.get('guests'):
        initial_data['guests_count'] = request.GET.get('guests')

    if request.method == 'POST':
        form = BookingForm(request.POST, listing=listing)
        if form.is_valid():
            check_in = form.cleaned_data['check_in']
            check_out = form.cleaned_data['check_out']
            guests_count = form.cleaned_data['guests_count']
            special_requests = form.cleaned_data['special_requests']

            delta = check_out - check_in
            nights = max(1, delta.days)
            pricing = listing.calculate_price_breakdown(nights)

            try:
                with transaction.atomic():
                    # Lock listing record to prevent concurrent double-booking
                    locked_listing = Listing.objects.select_for_update().get(id=listing.id)

                    # Check for overlapping active bookings
                    conflicting = Booking.objects.select_for_update().filter(
                        listing=locked_listing,
                        status__in=['confirmed', 'pending'],
                        check_in__lt=check_out,
                        check_out__gt=check_in,
                    )
                    if conflicting.exists():
                        messages.error(
                            request,
                            "Sorry! Another guest just booked these dates. Please choose different dates."
                        )
                        return redirect('listings:detail', slug=listing.slug)

                    # Create and confirm booking
                    booking = Booking(
                        listing=locked_listing,
                        guest=request.user,
                        check_in=check_in,
                        check_out=check_out,
                        guests_count=guests_count,
                        price_per_night=listing.price_per_night,
                        total_nights=nights,
                        subtotal=pricing['subtotal'],
                        service_fee=pricing['service_fee'],
                        cleaning_fee=pricing['cleaning_fee'],
                        total_amount=pricing['total_amount'],
                        status='confirmed',
                        payment_status='pay_at_property',
                        special_requests=special_requests,
                    )
                    booking.full_clean()
                    booking.save()

                messages.success(request, f"Your reservation is confirmed! Reference ID: {booking.booking_id}")
                return redirect('bookings:confirmation', booking_id=booking.booking_id)

            except ValidationError as ve:
                messages.error(request, str(ve))
            except Exception as e:
                messages.error(request, f"An unexpected error occurred while booking: {str(e)}")
        else:
            messages.error(request, "Please fix the errors in the booking form.")
    else:
        form = BookingForm(initial=initial_data, listing=listing)

    context = {
        'form': form,
        'listing': listing,
    }
    return render(request, 'bookings/create.html', context)


@login_required
def booking_confirmation_view(request, booking_id):
    """Displays reservation confirmation summary."""
    booking = get_object_or_404(
        Booking.objects.select_related('listing', 'listing__host', 'guest'),
        booking_id=booking_id
    )

    if booking.guest != request.user and booking.listing.host != request.user and not request.user.is_staff:
        raise PermissionDenied("You do not have access to view this booking.")

    return render(request, 'bookings/confirmation.html', {'booking': booking})


@login_required
def booking_detail_view(request, booking_id):
    """Displays detailed view of a booking for guest or host."""
    booking = get_object_or_404(
        Booking.objects.select_related('listing', 'listing__host', 'guest'),
        booking_id=booking_id
    )

    if booking.guest != request.user and booking.listing.host != request.user and not request.user.is_staff:
        raise PermissionDenied("You do not have access to view this booking.")

    is_host = (booking.listing.host == request.user)
    return render(request, 'bookings/detail.html', {'booking': booking, 'is_host': is_host})


@login_required
@require_POST
def booking_cancel_view(request, booking_id):
    """Allows guest or host to cancel an eligible reservation."""
    booking = get_object_or_404(Booking, booking_id=booking_id)

    if booking.guest != request.user and booking.listing.host != request.user and not request.user.is_staff:
        raise PermissionDenied("You cannot cancel this booking.")

    if not booking.can_cancel:
        messages.error(request, "This booking cannot be cancelled because it is in the past or already cancelled.")
        return redirect('bookings:detail', booking_id=booking.booking_id)

    reason = request.POST.get('cancellation_reason', 'Cancelled by user.')
    booking.status = 'cancelled'
    booking.cancellation_reason = reason
    booking.cancelled_at = timezone.now()
    booking.save(update_fields=['status', 'cancellation_reason', 'cancelled_at'])

    messages.info(request, f"Booking {booking.booking_id} has been cancelled successfully. Dates are now released.")
    if booking.listing.host == request.user:
        return redirect('accounts:host_dashboard')
    return redirect('accounts:guest_dashboard')


@require_GET
def calculate_price_api(request, slug):
    """
    JSON API used by the booking widget on listing detail page to dynamically calculate
    nights, subtotal, service fee, and total amount when dates change.
    """
    listing = get_object_or_404(Listing, slug=slug)
    check_in_str = request.GET.get('check_in')
    check_out_str = request.GET.get('check_out')

    if not check_in_str or not check_out_str:
        return JsonResponse({'error': 'Both check-in and check-out dates are required.'}, status=400)

    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    if check_out <= check_in:
        return JsonResponse({'error': 'Check-out must be after check-in.'}, status=400)

    delta = check_out - check_in
    nights = max(1, delta.days)
    breakdown = listing.calculate_price_breakdown(nights)

    # Check date availability
    has_conflict = Booking.objects.filter(
        listing=listing,
        status__in=['confirmed', 'pending'],
        check_in__lt=check_out,
        check_out__gt=check_in,
    ).exists()

    return JsonResponse({
        'nights': nights,
        'price_per_night': float(breakdown['price_per_night']),
        'subtotal': float(breakdown['subtotal']),
        'cleaning_fee': float(breakdown['cleaning_fee']),
        'service_fee': float(breakdown['service_fee']),
        'total_amount': float(breakdown['total_amount']),
        'is_available': not has_conflict,
    })
