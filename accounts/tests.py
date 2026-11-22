from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.profile_url = reverse('accounts:profile')

        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )

    def test_user_registration_success(self):
        response = self.client.post(self.register_url, {
            'first_name': 'New',
            'last_name': 'Guest',
            'username': 'newguest',
            'email': 'newguest@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'is_host': False,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newguest').exists())

    def test_duplicate_username_prevented(self):
        response = self.client.post(self.register_url, {
            'first_name': 'Another',
            'last_name': 'User',
            'username': 'testuser',  # Already exists
            'email': 'different@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'username', 'A user with that username already exists.')

    def test_duplicate_email_prevented(self):
        response = self.client.post(self.register_url, {
            'first_name': 'Another',
            'last_name': 'User',
            'username': 'uniqueuser',
            'email': 'testuser@example.com',  # Already exists
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', 'An account with this email address already exists.')

    def test_password_mismatch_prevented(self):
        response = self.client.post(self.register_url, {
            'first_name': 'New',
            'last_name': 'Guest',
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'Password12345!',
            'confirm_password': 'DifferentPassword999!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'confirm_password', 'Passwords do not match.')

    def test_user_login_success_with_username(self):
        response = self.client.post(self.login_url, {
            'username_or_email': 'testuser',
            'password': 'testpassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_user_login_success_with_email(self):
        response = self.client.post(self.login_url, {
            'username_or_email': 'testuser@example.com',
            'password': 'testpassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_invalid_login_rejected(self):
        response = self.client.post(self.login_url, {
            'username_or_email': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_user_logout(self):
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_unauthenticated_profile_redirects_to_login(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)
