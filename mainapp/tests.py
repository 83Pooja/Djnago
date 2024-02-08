from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Seller, Buyer


class SignupTestCase(TestCase):
    def test_signup_seller(self):
        response = self.client.post(reverse('signup'), {
            'accountType': 'seller',
            'name': 'John Doe',
            'username': 'johndoe',
            'email': 'johndoe@example.com',
            'mobile': '1234567890',
            'password': 'mypassword'
        })
        # Check if the response is a redirection
        self.assertEqual(response.status_code, 302)
        # Follow the redirection
        response = self.client.get(response.url)
        # Check if the response is a successful response
        self.assertEqual(response.status_code, 200)
        # Check if the URL matches the expected URL
        self.assertEqual(response.request['PATH_INFO'], '/profile/')

    def test_signup_buyer(self):
        response = self.client.post(reverse('signup'), {
            'accountType': 'buyer',
            'name': 'Jane Doe',
            'username': 'janedoe',
            'email': 'janedoe@example.com',
            'mobile': '9876543210',
            'password': 'mypassword'
        })
        # Check if the response is a redirection
        self.assertEqual(response.status_code, 302)
        # Follow the redirection
        response = self.client.get(response.url)
        # Check if the response is a successful response
        self.assertEqual(response.status_code, 200)
        # Check if the URL matches the expected URL
        self.assertEqual(response.request['PATH_INFO'], '/profile/')

    def test_signup_invalid_account_type(self):
        response = self.client.post(reverse('signup'), {
            'accountType': 'invalid',
            'name': 'Invalid User',
            'username': 'invaliduser',
            'email': 'invaliduser@example.com',
            'mobile': '9876543210',
            'password': 'mypassword'
        })
        # Check if the response is a successful response
        self.assertEqual(response.status_code, 200)
        # Check if the expected error message is present in the response content
        self.assertContains(response, 'Invalid account type')

