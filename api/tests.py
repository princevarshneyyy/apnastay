from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from listings.models import Listing
from bookings.models import Booking

User = get_user_model()


class APITests(APITestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            username='apihost',
            email='apihost@example.com',
            password='password123',
            is_host=True
        )
        self.guest = User.objects.create_user(
            username='apiguest',
            email='apiguest@example.com',
            password='password123'
        )

        self.listing = Listing.objects.create(
            host=self.host,
            title='Beachside Penthouse',
            property_type='apartment',
            address='Marine Drive',
            city='Mumbai',
            state='Maharashtra',
            country='India',
            price_per_night=Decimal('8000.00'),
            max_guests=4,
            is_active=True
        )

    def test_api_user_register(self):
        url = reverse('api:api_register')
        data = {
            'username': 'newapiuser',
            'email': 'newapi@example.com',
            'first_name': 'Api',
            'last_name': 'Tester',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'is_host': False,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertTrue(User.objects.filter(username='newapiuser').exists())

    def test_api_user_login(self):
        url = reverse('api:api_login')
        data = {
            'username': 'apiguest',
            'password': 'password123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_api_listing_list_and_search(self):
        url = reverse('api:api_listing_list_create')
        response = self.client.get(url, {'city': 'Mumbai'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_api_booking_create_authenticated(self):
        self.client.force_authenticate(user=self.guest)
        url = reverse('api:api_booking_list_create')

        today = timezone.now().date()
        data = {
            'listing': self.listing.id,
            'check_in': (today + timedelta(days=7)).isoformat(),
            'check_out': (today + timedelta(days=10)).isoformat(),
            'guests_count': 2,
            'special_requests': 'Quiet room please.'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking_id', response.data)
        self.assertEqual(response.data['total_nights'], 3)

    def test_api_wishlist_create_and_delete(self):
        self.client.force_authenticate(user=self.guest)
        list_url = reverse('api:api_wishlist_list_create')

        # Add to wishlist
        response = self.client.post(list_url, {'listing_id': self.listing.id}, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        wishlist_id = response.data['id']

        # Delete from wishlist
        delete_url = reverse('api:api_wishlist_delete', kwargs={'pk': wishlist_id})
        del_resp = self.client.delete(delete_url)
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
