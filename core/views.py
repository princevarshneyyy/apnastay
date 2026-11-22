from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Avg
from django.http import JsonResponse
from django.db import connection
from django.conf import settings

from listings.models import Listing
from reviews.models import Review
from .forms import ContactForm
from .models import ContactMessage


def home_view(request):
    """
    Homepage displaying hero search, category icons, featured listings,
    popular Indian destinations, recently added properties, and testimonials.
    All data is queried dynamically from the database.
    """
    # Featured listings
    featured_listings = Listing.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('host').prefetch_related('images')[:6]

    # If not enough featured, fill with top-rated
    if featured_listings.count() < 3:
        featured_listings = Listing.objects.filter(
            is_active=True
        ).select_related('host').prefetch_related('images')[:6]

    # Recently added stays
    recent_listings = Listing.objects.filter(
        is_active=True
    ).select_related('host').prefetch_related('images').order_by('-created_at')[:6]

    # Popular destinations with dynamic listing counts
    destination_names = ['Goa', 'Manali', 'Jaipur', 'Udaipur', 'Kerala', 'Rishikesh']
    popular_destinations = []
    destination_photos = {
        'Goa': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=600&auto=format&fit=crop&q=80',
        'Manali': 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=600&auto=format&fit=crop&q=80',
        'Jaipur': 'https://images.unsplash.com/photo-1477587458883-47145ed94245?w=600&auto=format&fit=crop&q=80',
        'Udaipur': 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=600&auto=format&fit=crop&q=80',
        'Kerala': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=600&auto=format&fit=crop&q=80',
        'Rishikesh': 'https://images.unsplash.com/photo-1544717305-2782549b5136?w=600&auto=format&fit=crop&q=80',
    }

    for dest in destination_names:
        count = Listing.objects.filter(is_active=True, city__icontains=dest).count()
        popular_destinations.append({
            'name': dest,
            'count': count,
            'image': destination_photos.get(dest, 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600')
        })

    # Verified recent reviews for testimonials section
    testimonials = Review.objects.select_related('user', 'listing').filter(rating__gte=4).order_by('-created_at')[:4]

    context = {
        'featured_listings': featured_listings,
        'recent_listings': recent_listings,
        'popular_destinations': popular_destinations,
        'testimonials': testimonials,
    }
    return render(request, 'core/home.html', context)


def contact_view(request):
    """Handles contact and support inquiry submissions."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent to the ApnaStay Support Team. We will reply via email shortly.")
            return redirect('core:contact')
        else:
            messages.error(request, "Please fill out all required fields correctly.")
    else:
        form = ContactForm()

    return render(request, 'core/contact.html', {'form': form})


def about_view(request):
    return render(request, 'core/about.html')


def help_view(request):
    return render(request, 'core/help.html')


def terms_view(request):
    return render(request, 'core/terms.html')


def privacy_view(request):
    return render(request, 'core/privacy.html')


def health_check_view(request):
    """
    Health check endpoint returning database engine and system status.
    Useful for demonstration during project viva.
    """
    db_engine = settings.DATABASES['default'].get('ENGINE', '')
    is_postgres = 'postgresql' in db_engine
    status = 'healthy'
    db_version = 'unknown'

    try:
        with connection.cursor() as cursor:
            if is_postgres:
                cursor.execute("SELECT version();")
            else:
                cursor.execute("SELECT sqlite_version();")
            row = cursor.fetchone()
            db_version = row[0] if row else 'connected'
    except Exception as e:
        status = f"unhealthy: {str(e)}"

    return JsonResponse({
        'status': status,
        'platform': 'ApnaStay',
        'database': {
            'engine': db_engine,
            'is_postgresql': is_postgres,
            'version': db_version,
            'name': str(settings.DATABASES['default'].get('NAME')),
        }
    })


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_403(request, exception=None):
    return render(request, '403.html', status=403)


def custom_500(request):
    return render(request, '500.html', status=500)

