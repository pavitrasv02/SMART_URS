from django.test import TestCase, Client
from django.urls import reverse
from .models import User, ServiceProvider, Service, Booking, Review

class CoreViewsTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(
            name="Test User",
            email="test@example.com",
            phone="1234567890",
            password="pass123",
            address="123 Test St"
        )
        # Create a provider and service
        self.provider = ServiceProvider.objects.create(
            name="Alice",
            email="alice@example.com",
            phone="1112223333",
            password="pwd",
            service_type="Plumbing",
            location="City",
        )
        self.service = Service.objects.create(
            name="Fix Leak",
            description="Fixes leaks",
            price=500
        )
        self.client = Client()

    def test_signup_and_login(self):
        # Sign up a new user
        resp = self.client.post(reverse('signup'), {
            'name': 'Bob',
            'email': 'bob@example.com',
            'phone': '9998887777',
            'address': '456 Bob St',
            'password': 'bobpass',
            'confirm_password': 'bobpass'
        })
        self.assertRedirects(resp, reverse('home'))
        # Log in as Bob
        resp = self.client.post(reverse('login'), {
            'email': 'bob@example.com',
            'password': 'bobpass'
        })
        self.assertRedirects(resp, reverse('home'))

    def test_booking_flow(self):
        # Log in
        self.client.post(reverse('login'), {'email': self.user.email, 'password': 'pass123'})
        # Book a service
        resp = self.client.post(
            reverse('book_provider', args=[self.provider.id]),
            {
                'name': self.user.name,
                'email': self.user.email,
                'phone': self.user.phone,
                'address': self.user.address,
                'service': self.service.id,
                'booking_date': '2025-05-10',
                'booking_time': '10:00'
            }
        )
        self.assertRedirects(resp, reverse('booking_success'))
        # Verify booking exists
        booking = Booking.objects.get(user=self.user, provider=self.provider)
        self.assertEqual(booking.status, 'Pending')

    def test_leave_review(self):
        # Create a completed booking
        booking = Booking.objects.create(
            user=self.user, provider=self.provider, service=self.service,
            booking_date='2025-05-10', booking_time='10:00', status='Completed'
        )
        # Log in and leave a review
        self.client.post(reverse('login'), {'email': self.user.email, 'password': 'pass123'})
        resp = self.client.post(
            reverse('leave_review', args=[booking.id]),
            {'rating': '4', 'comment': 'Great job!'}
        )
        self.assertRedirects(resp, reverse('my_bookings'))
        # Check review
        review = Review.objects.get(booking=booking)
        self.assertEqual(review.rating, 4)
