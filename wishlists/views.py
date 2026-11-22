from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Wishlist
from listings.models import Listing


@login_required
def wishlist_list_view(request):
    """Displays the user's saved favourite properties."""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('listing', 'listing__host').prefetch_related('listing__images')
    return render(request, 'wishlists/list.html', {'wishlist_items': wishlist_items})


@login_required
@require_POST
def wishlist_toggle_view(request, listing_id):
    """
    Toggles a property in/out of the user's wishlist.
    Works with both AJAX requests and standard form submissions.
    """
    listing = get_object_or_404(Listing, id=listing_id)
    existing = Wishlist.objects.filter(user=request.user, listing=listing).first()

    if existing:
        existing.delete()
        is_added = False
        message = f"Removed '{listing.title}' from your Wishlist."
    else:
        Wishlist.objects.create(user=request.user, listing=listing)
        is_added = True
        message = f"Saved '{listing.title}' to your Wishlist!"

    total_count = Wishlist.objects.filter(user=request.user).count()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'success': True,
            'is_added': is_added,
            'message': message,
            'wishlist_count': total_count
        })

    messages.success(request, message)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    return redirect(next_url or 'wishlists:list')
