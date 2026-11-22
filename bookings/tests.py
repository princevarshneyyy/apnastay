from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from listings.models import Listing
from bookings.models import Booking

User = get_user_model()


class BookingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(
            username='hostuser',
            email='hostuser@example.com',
            password='password123',
            is_host=True
        )
        self.guest = User.objects.create_user(
            username='guestuser',
            email='guest@example.com',
            password='password123'
        )
        self.other_guest = User.objects.create_user(
            username='otherguest',
            email='otherguest@example.com',
            password='password123'
        )

        self.listing = Listing.objects.create(
            host=self.host,
            title='Seaside Villa',
            property_type='villa',
            address='Calangute',
            city='Goa',
            state='Goa',
            country='India',
            price_per_night=Decimal('5000.00'),
            cleaning_fee=Decimal('500.00'),
            max_guests=4,
            is_active=True
        )

        self.today = timezone.now().date()

    def test_booking_creation_success(self):
        self.client.login(username='guestuser', password='password123')
        create_url = reverse('bookings:create', kwargs={'slug': self.listing.slug})

        check_in = self.today + timedelta(days=5)
        check_out = self.today + timedelta(days=8)

        response = self.client.post(create_url, {
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'guests_count': 2,
            'special_requests': 'Late check-in please.'
        })
        self.assertEqual(response.status_code, 302)

        booking = Booking.objects.filter(guest=self.guest, listing=self.listing).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.total_nights, 3)
        self.assertEqual(booking.subtotal, Decimal('15000.00')) # 5000 * 3
        self.assertEqual(booking.status, 'confirmed')

    def test_overlapping_booking_prevented(self):
        # Create an existing confirmed booking from day 5 to day 10
        check_in = self.today + timedelta(days=5)
        check_out = self.today + timedelta(days=10)

        Booking.objects.create(
            listing=self.listing,
            guest=self.guest,
            check_in=check_in,
            check_out=check_out,
            guests_count=2,
            price_per_night=Decimal('5000.00'),
            subtotal=Decimal('25000.00'),
            total_amount=Decimal('26500.00'),
            status='confirmed'
        )

        # Another guest attempts to book overlapping dates (day 7 to day 12)
        self.client.login(username='otherguest', password='password123')
        create_url = reverse('bookings:create', kwargs={'slug': self.listing.slug})

        overlap_check_in = self.today + timedelta(days=7)
        overlap_check_out = self.today + timedelta(days=12)

        response = self.client.post(create_url, {
            'check_in': overlap_check_in.isoformat(),
            'check_out': overlap_check_out.isoformat(),
            'guests_count': 2,
        })
        # Should redirect back to detail view with error
        self.assertEqual(response.status_code, 302)
        # Verify second booking was NOT created
        self.assertFalse(Booking.objects.filter(guest=self.other_guest).exists())

    def test_past_date_booking_rejected(self):
        self.client.login(username='guestuser', password='password123')
        create_url = reverse('bookings:create', kwargs={'slug': self.listing.slug})

        past_check_in = self.today - timedelta(days=5)
        past_check_out = self.today + timedelta(days=2)

        response = self.client.post(create_url, {
            'check_in': past_check_in.isoformat(),
            'check_out': past_check_out.isoformat(),
            'guests_count': 2,
        })
        self.assertEqual(response.status_code, 200) # Form re-rendered with error
        self.assertFalse(Booking.objects.filter(guest=self.guest).exists())

    def test_checkout_before_checkin_rejected(self):
        self.client.login(username='guestuser', password='password123')
        create_url = reverse('bookings:create', kwargs={'slug': self.listing.slug})

        check_in = self.today + timedelta(days=5)
        check_out = self.today + timedelta(days=3)

        response = self.client.post(create_url, {
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'guests_count': 2,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.filter(guest=self.guest).exists())

    def test_host_cannot_book_own_property(self):
        self.client.login(username='hostuser', password='password123')
        create_url = reverse('bookings:create', kwargs={'slug': self.listing.slug})

        check_in = self.today + timedelta(days=5)
        check_out = self.today + timedelta(days=8)

        response = self.client.post(create_url, {
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'guests_count': 2,
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Booking.objects.filter(guest=self.host).exists())

    def test_booking_cancellation(self):
        self.client.login(username='guestuser', password='password123')

        check_in = self.today + timedelta(days=10)
        check_out = self.today + timedelta(days=15)

        booking = Booking.objects.create(
            listing=self.listing,
            guest=self.guest,
            check_in=check_in,
            check_out=check_out,
            guests_count=2,
            price_per_night=Decimal('5000.00'),
            subtotal=Decimal('25000.00'),
            total_amount=Decimal('26500.00'),
            status='confirmed'
        )

        cancel_url = reverse('bookings:cancel', kwargs={'booking_id': booking.booking_id})
        response = self.client.post(cancel_url, {'cancellation_reason': 'Changed travel plans.'})
        self.assertEqual(response.status_code, 302)

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertIsNotNone(booking.cancelled_at)
