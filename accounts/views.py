from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm
from .models import User
from listings.models import Listing
from bookings.models import Booking
from reviews.models import Review
from wishlists.models import Wishlist


def register_view(request):
    """Handles guest/host user registration."""
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to ApnaStay, {user.first_name}! Your account has been created.")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('core:home')
        else:
            messages.error(request, "Please fix the errors below to register.")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Handles login via username or email."""
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.user
            login(request, user)
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Browser-session only
            else:
                request.session.set_expiry(1209600)  # 2 weeks

            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('core:home')
        else:
            messages.error(request, "Invalid username/email or password.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Logs out the active user."""
    logout(request)
    messages.info(request, "You have been logged out. See you next time!")
    return redirect('core:home')


@login_required
def profile_view(request):
    """Allows user to view and edit profile details & profile picture."""
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been successfully updated.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors in the profile form.")
    else:
        form = UserProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    """Allows authenticated user to change their password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Prevent user from being logged out
            messages.success(request, "Your password has been changed successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def become_host_view(request):
    """Toggles or enables host status for a user."""
    user = request.user
    if not user.is_host:
        user.is_host = True
        user.save()
        messages.success(request, "Congratulations! You are now registered as an ApnaStay Host. You can list your first property.")
    return redirect('listings:create')


@login_required
def guest_dashboard_view(request):
    """Displays comprehensive guest trip history, bookings, and stats."""
    user = request.user
    today = timezone.now().date()

    user_bookings = Booking.objects.filter(guest=user).select_related('listing', 'listing__host').order_by('-created_at')

    upcoming_bookings = user_bookings.filter(check_in__gte=today, status__in=['pending', 'confirmed'])
    completed_bookings = user_bookings.filter(Q(status='completed') | Q(check_out__lt=today, status='confirmed'))
    cancelled_bookings = user_bookings.filter(status='cancelled')

    wishlist_items = Wishlist.objects.filter(user=user).select_related('listing').order_by('-created_at')
    user_reviews = Review.objects.filter(user=user).select_related('listing').order_by('-created_at')

    context = {
        'total_bookings': user_bookings.count(),
        'upcoming_bookings': upcoming_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'wishlist_items': wishlist_items,
        'user_reviews': user_reviews,
    }
    return render(request, 'accounts/guest_dashboard.html', context)


@login_required
def host_dashboard_view(request):
    """Displays host property listings, incoming reservations, and revenue analytics."""
    user = request.user
    if not user.is_host and not user.listings.exists():
        messages.info(request, "Become a host first to access the Host Dashboard.")
        return redirect('accounts:become_host')

    host_listings = Listing.objects.filter(host=user).annotate(
        total_bookings_count=Count('bookings'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-created_at')

    # All bookings for this host's properties
    host_reservations = Booking.objects.filter(listing__host=user).select_related('listing', 'guest').order_by('-created_at')

    today = timezone.now().date()
    upcoming_reservations = host_reservations.filter(check_in__gte=today, status__in=['pending', 'confirmed'])

    # Total confirmed/completed revenue
    revenue_agg = host_reservations.filter(status__in=['confirmed', 'completed']).aggregate(total=Sum('subtotal'))
    total_revenue = revenue_agg['total'] or 0

    context = {
        'host_listings': host_listings,
        'total_listings_count': host_listings.count(),
        'active_listings_count': host_listings.filter(is_active=True).count(),
        'host_reservations': host_reservations,
        'upcoming_reservations': upcoming_reservations,
        'total_reservations_count': host_reservations.count(),
        'total_revenue': total_revenue,
    }
    return render(request, 'accounts/host_dashboard.html', context)
