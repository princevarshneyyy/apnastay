from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import Listing, Amenity

User = get_user_model()


class ListingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(
            username='hostuser',
            email='hostuser@example.com',
            password='password123',
            is_host=True
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        self.listing = Listing.objects.create(
            host=self.host,
            title='Goa Sunshine Villa',
            property_type='villa',
            address='12 Beach Rd',
            city='Goa',
            state='Goa',
            country='India',
            price_per_night=Decimal('5000.00'),
            max_guests=4,
            bedrooms=2,
            beds=2,
            bathrooms=2,
            is_active=True
        )

    def test_listing_creation_authenticated_host(self):
        self.client.login(username='hostuser', password='password123')
        create_url = reverse('listings:create')
        response = self.client.post(create_url, {
            'title': 'New Mountain Hut',
            'property_type': 'cabin',
            'description': 'Beautiful cedar hut with fireplace.',
            'address': 'Solang Valley',
            'city': 'Manali',
            'state': 'Himachal Pradesh',
            'country': 'India',
            'price_per_night': '4000.00',
            'max_guests': 2,
            'bedrooms': 1,
            'beds': 1,
            'bathrooms': 1,
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Listing.objects.filter(title='New Mountain Hut').exists())

    def test_listing_edit_permission_owner(self):
        self.client.login(username='hostuser', password='password123')
        edit_url = reverse('listings:edit', kwargs={'slug': self.listing.slug})
        response = self.client.post(edit_url, {
            'title': 'Goa Sunshine Villa - Updated',
            'property_type': 'villa',
            'description': 'Now with upgraded pool.',
            'address': self.listing.address,
            'city': self.listing.city,
            'state': self.listing.state,
            'country': 'India',
            'price_per_night': '6000.00',
            'max_guests': 4,
            'bedrooms': 2,
            'beds': 2,
            'bathrooms': 2,
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Goa Sunshine Villa - Updated')
        self.assertEqual(self.listing.price_per_night, Decimal('6000.00'))

    def test_listing_edit_permission_denied_for_non_owner(self):
        self.client.login(username='otheruser', password='password123')
        edit_url = reverse('listings:edit', kwargs={'slug': self.listing.slug})
        response = self.client.post(edit_url, {
            'title': 'Hacked Title',
            'property_type': 'villa',
            'description': 'Malicious update.',
            'address': self.listing.address,
            'city': self.listing.city,
            'state': self.listing.state,
            'country': 'India',
            'price_per_night': '100.00',
            'max_guests': 4,
            'bedrooms': 2,
            'beds': 2,
            'bathrooms': 2,
        })
        self.assertEqual(response.status_code, 403)
        self.listing.refresh_from_db()
        self.assertNotEqual(self.listing.title, 'Hacked Title')

    def test_listing_search_and_filtering(self):
        # Create second listing in different city and category
        Listing.objects.create(
            host=self.host,
            title='Jaipur Heritage Suite',
            property_type='apartment',
            address='Johari Bazar',
            city='Jaipur',
            state='Rajasthan',
            country='India',
            price_per_night=Decimal('2500.00'),
            max_guests=2,
            is_active=True
        )

        list_url = reverse('listings:list')

        # Filter by city
        response = self.client.get(list_url, {'q': 'Jaipur'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jaipur Heritage Suite')
        self.assertNotContains(response, 'Goa Sunshine Villa')

        # Filter by category
        response = self.client.get(list_url, {'category': 'villa'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Goa Sunshine Villa')
        self.assertNotContains(response, 'Jaipur Heritage Suite')

        # Filter by max price
        response = self.client.get(list_url, {'max_price': '3000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jaipur Heritage Suite')
        self.assertNotContains(response, 'Goa Sunshine Villa')
