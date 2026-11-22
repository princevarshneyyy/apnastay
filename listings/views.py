from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Listing, ListingImage, Amenity
from .forms import ListingForm, ListingImageForm
from reviews.models import Review
from bookings.models import Booking


def listing_list_view(request):
    """
    Search and filter properties dynamically using Django ORM.
    Supports destination, category, price range, guest capacity, amenities, and sorting.
    """
    queryset = Listing.objects.filter(is_active=True).select_related('host').prefetch_related('images', 'amenities')

    # Keyword / Destination search
    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(
            Q(city__icontains=query) |
            Q(state__icontains=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query)
        )

    # Destination parameter (from homepage search bar)
    destination = request.GET.get('destination', '').strip()
    if destination:
        queryset = queryset.filter(
            Q(city__icontains=destination) |
            Q(state__icontains=destination) |
            Q(title__icontains=destination)
        )

    # Category / Property Type filter
    category = request.GET.get('category', '').strip()
    if category:
        queryset = queryset.filter(property_type__iexact=category)

    # Guest capacity filter
    guests = request.GET.get('guests')
    if guests and guests.isdigit():
        queryset = queryset.filter(max_guests__gte=int(guests))

    # Min and Max Price filters
    min_price = request.GET.get('min_price')
    if min_price and min_price.isdigit():
        queryset = queryset.filter(price_per_night__gte=float(min_price))

    max_price = request.GET.get('max_price')
    if max_price and max_price.isdigit():
        queryset = queryset.filter(price_per_night__lte=float(max_price))

    # Amenities filter (multiple)
    selected_amenities = request.GET.getlist('amenity')
    if selected_amenities:
        for amen in selected_amenities:
            queryset = queryset.filter(amenities__name__iexact=amen)

    # Minimum Rating filter
    min_rating = request.GET.get('min_rating')
    if min_rating:
        queryset = queryset.annotate(avg_r=Avg('reviews__rating')).filter(avg_r__gte=float(min_rating))

    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        queryset = queryset.order_by('price_per_night')
    elif sort == 'price_high':
        queryset = queryset.order_by('-price_per_night')
    elif sort == 'rating':
        queryset = queryset.annotate(avg_r=Avg('reviews__rating')).order_by('-avg_r', '-created_at')
    else:  # newest default
        queryset = queryset.order_by('-created_at')

    # Distinct to avoid duplicates from M2M joins
    queryset = queryset.distinct()

    # Pagination: 9 listings per page
    paginator = Paginator(queryset, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_amenities = Amenity.objects.all()

    context = {
        'listings': page_obj,
        'page_obj': page_obj,
        'total_count': paginator.count,
        'query': query or destination,
        'category': category,
        'min_price': min_price,
        'max_price': max_price,
        'guests': guests,
        'sort': sort,
        'all_amenities': all_amenities,
        'selected_amenities': selected_amenities,
    }
    return render(request, 'listings/list.html', context)


def listing_detail_view(request, slug):
    """
    Displays full details of a listing, gallery, amenities, host, reviews, and booking widget.
    """
    listing = get_object_or_404(
        Listing.objects.select_related('host').prefetch_related('images', 'amenities'),
        slug=slug
    )

    # Get reviews
    reviews = listing.reviews.select_related('user').order_by('-created_at')

    # Check if user has an active/completed booking to review
    can_user_review = False
    eligible_booking = None
    if request.user.is_authenticated and request.user != listing.host:
        eligible_booking = Booking.objects.filter(
            listing=listing,
            guest=request.user,
            review__isnull=True
        ).filter(
            Q(status='completed') | Q(status='confirmed')
        ).first()
        if eligible_booking and eligible_booking.can_review:
            can_user_review = True

    # Check if property is wishlisted
    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = listing.wishlisted_by.filter(user=request.user).exists()

    # Similar listings in same city/category
    similar_listings = Listing.objects.filter(
        is_active=True,
        city__iexact=listing.city
    ).exclude(id=listing.id)[:3]

    context = {
        'listing': listing,
        'images': listing.images.all(),
        'amenities': listing.amenities.all(),
        'reviews': reviews,
        'can_user_review': can_user_review,
        'eligible_booking': eligible_booking,
        'is_wishlisted': is_wishlisted,
        'similar_listings': similar_listings,
    }
    return render(request, 'listings/detail.html', context)


@login_required
def listing_create_view(request):
    """Allows a host to create a new property listing with multiple image uploads."""
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.host = request.user
            listing.save()
            form.save_m2m()  # Save amenities

            # Ensure user is marked as host
            if not request.user.is_host:
                request.user.is_host = True
                request.user.save()

            # Handle multiple image uploads
            uploaded_images = request.FILES.getlist('images')
            for index, img_file in enumerate(uploaded_images):
                ListingImage.objects.create(
                    listing=listing,
                    image=img_file,
                    is_cover=(index == 0)  # First image is cover
                )

            messages.success(request, f"Property '{listing.title}' created successfully!")
            return redirect('listings:detail', slug=listing.slug)
        else:
            messages.error(request, "Please review the errors below.")
    else:
        form = ListingForm()

    return render(request, 'listings/form.html', {'form': form, 'title': 'List Your Property'})


@login_required
def listing_update_view(request, slug):
    """Allows only the host owner to edit listing details."""
    listing = get_object_or_404(Listing, slug=slug)

    # Permission check: Only owner or staff can edit
    if listing.host != request.user and not request.user.is_staff:
        raise PermissionDenied("You do not have permission to edit this listing.")

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            listing = form.save()

            # Add newly uploaded images if any
            uploaded_images = request.FILES.getlist('images')
            has_cover = listing.images.filter(is_cover=True).exists()
            for index, img_file in enumerate(uploaded_images):
                ListingImage.objects.create(
                    listing=listing,
                    image=img_file,
                    is_cover=(not has_cover and index == 0)
                )

            messages.success(request, f"'{listing.title}' has been updated.")
            return redirect('listings:detail', slug=listing.slug)
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = ListingForm(instance=listing)

    return render(request, 'listings/form.html', {
        'form': form,
        'listing': listing,
        'title': f"Edit {listing.title}",
        'is_edit': True,
        'images': listing.images.all()
    })


@login_required
def listing_delete_view(request, slug):
    """Allows only the host owner to delete the property listing."""
    listing = get_object_or_404(Listing, slug=slug)

    if listing.host != request.user and not request.user.is_staff:
        raise PermissionDenied("You do not have permission to delete this listing.")

    if request.method == 'POST':
        title = listing.title
        listing.delete()
        messages.success(request, f"Listing '{title}' has been successfully deleted.")
        return redirect('accounts:host_dashboard')

    return render(request, 'listings/confirm_delete.html', {'listing': listing})


@login_required
@require_POST
def listing_toggle_status_view(request, slug):
    """Quickly toggle listing availability between active and inactive."""
    listing = get_object_or_404(Listing, slug=slug)

    if listing.host != request.user and not request.user.is_staff:
        raise PermissionDenied("You do not have permission to modify this listing.")

    listing.is_active = not listing.is_active
    listing.save(update_fields=['is_active'])

    status_str = "Active" if listing.is_active else "Inactive (Hidden)"
    messages.info(request, f"Listing '{listing.title}' is now {status_str}.")
    return redirect('accounts:host_dashboard')


@login_required
@require_POST
def set_cover_image_view(request, listing_id, image_id):
    """Sets a specific image as the cover image for the listing."""
    listing = get_object_or_404(Listing, id=listing_id)
    if listing.host != request.user and not request.user.is_staff:
        raise PermissionDenied()

    image = get_object_or_404(ListingImage, id=image_id, listing=listing)
    listing.images.update(is_cover=False)
    image.is_cover = True
    image.save(update_fields=['is_cover'])

    messages.success(request, "Cover image updated successfully.")
    return redirect('listings:edit', slug=listing.slug)


@login_required
@require_POST
def delete_image_view(request, listing_id, image_id):
    """Deletes an image from the listing's gallery."""
    listing = get_object_or_404(Listing, id=listing_id)
    if listing.host != request.user and not request.user.is_staff:
        raise PermissionDenied()

    image = get_object_or_404(ListingImage, id=image_id, listing=listing)
    was_cover = image.is_cover
    image.delete()

    # If deleted image was cover, assign cover to first available image
    if was_cover:
        next_image = listing.images.first()
        if next_image:
            next_image.is_cover = True
            next_image.save(update_fields=['is_cover'])

    messages.info(request, "Image deleted.")
    return redirect('listings:edit', slug=listing.slug)
