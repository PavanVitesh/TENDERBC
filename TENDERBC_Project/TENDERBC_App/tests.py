from django.test import TestCase
import unittest2
from django.urls import reverse
from .models import User

# Create your tests here.


# class PastBidsTestCase(TestCase):
#     def setUp(self):
#         self.user = User.objects.create(username='Vitesh')
#         self.tender = Tender.objects.create(title='Test Tender', description='Test Description', Status='Completed')
#         self.bid = Bid.objects.create(bidder_id=self.user.id, tender_id=self.tender.id, Status='Submitted')

#     def test_past_bids(self):
#         self.client.force_login(self.user)
#         response = self.client.get(reverse('past_bids'))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'html/past_bids.html')
#         self.assertContains(response, 'Test Tender')
#         self.assertNotContains(response, 'Nonexistent Tender')
#         self.assertEqual(len(response.context['submitted_tenders']), 1)
#         self.assertEqual(response.context['submitted_tenders'][0].title, 'Test Tender')
#         self.assertEqual(response.context['submitted_tenders'][0].description, 'Test Description')
#         self.assertEqual(response.context['submitted_tenders'][0].Status, 'Completed')
#         self.assertEqual(response.context['submitted_tenders'][0].id, self.tender.id)
#         self.client.logout()



class LoginTestCase(TestCase):
    def setUp(self):
        self.url = reverse('login')
        self.username = 'Vitesh'
        self.password = 'Pavan@123'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_login_success(self):
        response = self.client.post(self.url, {'username': self.username, 'password': self.password})
        self.assertEqual(response.status_code, 302)  # Redirects to home page
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_failure(self):
        response = self.client.post(self.url, {'username': self.username, 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)  # Login page is rendered again
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, 'Invalid Credentials')