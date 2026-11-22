from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from listings.models import Listing
from bookings.models import Booking
from reviews.models import Review

User = get_user_model()


class ReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username='hostuser', email='host@example.com', password='password123', is_host=True)
        self.guest = User.objects.create_user(username='guestuser', email='guest@example.com', password='password123')
        self.unbooked_user = User.objects.create_user(username='unbooked', email='unbooked@example.com', password='password123')

        self.listing = Listing.objects.create(
            host=self.host,
            title='Beachfront Cottage',
            property_type='cottage',
            address='Sunset Strip',
            city='Goa',
            state='Goa',
            country='India',
            price_per_night=Decimal('4000.00'),
            max_guests=4,
            is_active=True
        )

        self.today = timezone.now().date()

        # Create a completed booking for guest
        self.completed_booking = Booking.objects.create(
            listing=self.listing,
            guest=self.guest,
            check_in=self.today - timedelta(days=10),
            check_out=self.today - timedelta(days=7),
            guests_count=2,
            price_per_night=Decimal('4000.00'),
            subtotal=Decimal('12000.00'),
            total_amount=Decimal('12600.00'),
            status='completed'
        )

    def test_review_submission_for_completed_stay(self):
        self.client.login(username='guestuser', password='password123')
        create_url = reverse('reviews:create', kwargs={'booking_id': self.completed_booking.booking_id})

        response = self.client.post(create_url, {
            'rating': 5,
            'comment': 'Stunning cottage and excellent cleanliness!'
        })
        self.assertEqual(response.status_code, 302)

        review = Review.objects.filter(booking=self.completed_booking).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)
        self.assertEqual(self.listing.average_rating, 5.0)

    def test_unbooked_user_cannot_review(self):
        self.client.login(username='unbooked', password='password123')
        create_url = reverse('reviews:create', kwargs={'booking_id': self.completed_booking.booking_id})

        response = self.client.post(create_url, {
            'rating': 1,
            'comment': 'Fake review.'
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Review.objects.filter(user=self.unbooked_user).exists())

    def test_host_cannot_review_own_property(self):
        self.client.login(username='hostuser', password='password123')
        create_url = reverse('reviews:create', kwargs={'booking_id': self.completed_booking.booking_id})

        response = self.client.post(create_url, {
            'rating': 5,
            'comment': 'Self praise.'
        })
        self.assertEqual(response.status_code, 403)

    def test_duplicate_review_prevented_per_booking(self):
        Review.objects.create(
            listing=self.listing,
            booking=self.completed_booking,
            user=self.guest,
            rating=4,
            comment='Good stay.'
        )

        self.client.login(username='guestuser', password='password123')
        create_url = reverse('reviews:create', kwargs={'booking_id': self.completed_booking.booking_id})

        response = self.client.post(create_url, {
            'rating': 5,
            'comment': 'Trying second review for same booking.'
        })
        self.assertEqual(response.status_code, 302)
        # Verify still only one review exists
        self.assertEqual(Review.objects.filter(booking=self.completed_booking).count(), 1)
