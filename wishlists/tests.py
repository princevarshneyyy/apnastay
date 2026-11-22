from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from listings.models import Listing
from wishlists.models import Wishlist

User = get_user_model()


class WishlistTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='wishuser', email='wish@example.com', password='password123')
        self.host = User.objects.create_user(username='hostuser', email='host@example.com', password='password123', is_host=True)

        self.listing = Listing.objects.create(
            host=self.host,
            title='Romantic Treehouse',
            property_type='unique',
            address='Forest Edge',
            city='Wayanad',
            state='Kerala',
            country='India',
            price_per_night=Decimal('6500.00'),
            is_active=True
        )

    def test_wishlist_toggle_add_and_remove(self):
        self.client.login(username='wishuser', password='password123')
        toggle_url = reverse('wishlists:toggle', kwargs={'listing_id': self.listing.id})

        # 1. First toggle -> Adds to wishlist
        response = self.client.post(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data['is_added'])
        self.assertTrue(Wishlist.objects.filter(user=self.user, listing=self.listing).exists())

        # 2. Second toggle -> Removes from wishlist
        response = self.client.post(toggle_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertFalse(json_data['is_added'])
        self.assertFalse(Wishlist.objects.filter(user=self.user, listing=self.listing).exists())

    def test_unauthenticated_wishlist_toggle_redirects(self):
        toggle_url = reverse('wishlists:toggle', kwargs={'listing_id': self.listing.id})
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, 302)
