from django.conf import settings

def global_context(request):
    """
    Context processor providing global variables across all templates.
    """
    context = {
        'PLATFORM_NAME': 'ApnaStay',
        'PLATFORM_TAGLINE': 'Apna Stay, Apni Choice.',
        'ACTIVE_DB': getattr(settings, 'ACTIVE_DB', 'sqlite'),
        'PROPERTY_CATEGORIES': [
            {'code': 'apartment', 'name': 'Apartments', 'icon': 'bi-building'},
            {'code': 'villa', 'name': 'Villas', 'icon': 'bi-house-heart'},
            {'code': 'farmhouse', 'name': 'Farmhouses', 'icon': 'bi-tree'},
            {'code': 'cottage', 'name': 'Cottages', 'icon': 'bi-house-door'},
            {'code': 'homestay', 'name': 'Homestays', 'icon': 'bi-people'},
            {'code': 'resort', 'name': 'Resorts', 'icon': 'bi-water'},
            {'code': 'cabin', 'name': 'Cabins', 'icon': 'bi-snow'},
            {'code': 'unique', 'name': 'Unique Stays', 'icon': 'bi-stars'},
        ],
        'wishlist_count': 0,
        'user_wishlist_ids': [],
    }

    if request.user.is_authenticated:
        try:
            from wishlists.models import Wishlist
            user_wishlists = Wishlist.objects.filter(user=request.user).values_list('listing_id', flat=True)
            context['wishlist_count'] = len(user_wishlists)
            context['user_wishlist_ids'] = list(user_wishlists)
        except Exception:
            context['wishlist_count'] = 0
            context['user_wishlist_ids'] = []

    return context
