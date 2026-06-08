from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Payment, Booking, User, ServiceProvider, Service
import uuid

class Command(BaseCommand):
    help = 'Create sample payment data for testing the admin interface'

    def handle(self, *args, **options):
        # Get or create some sample bookings first
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'name': 'Test User',
                'phone': '1234567890',
                'address': 'Test Address',
                'password': 'testpass'
            }
        )
        
        provider, created = ServiceProvider.objects.get_or_create(
            email='provider@example.com',
            defaults={
                'name': 'Test Provider',
                'phone': '0987654321',
                'service_type': 'cleaning',
                'location': 'Test Location',
                'password': 'providerpass',
                'availability': True,
                'rating': 4.5
            }
        )
        
        service, created = Service.objects.get_or_create(
            name='House Cleaning',
            defaults={
                'service_type': 'cleaning',
                'description': 'Professional house cleaning service',
                'base_price': 1500,
                'duration_hours': 3
            }
        )
        
        # Create sample bookings if they don't exist
        bookings = []
        for i in range(5):
            booking, created = Booking.objects.get_or_create(
                user=user,
                provider=provider,
                service=service,
                booking_date=timezone.now().date(),
                booking_time=timezone.now().time(),
                defaults={
                    'status': 'Completed',
                    'address': f'Test Address {i+1}'
                }
            )
            bookings.append(booking)
        
        # Create sample payments
        payment_modes = ['googlepay', 'phonepe', 'paytm', 'debitcard', 'creditcard', 'cod', 'paylater']
        payment_statuses = ['completed', 'pending', 'processing']
        
        for i, booking in enumerate(bookings):
            mode = payment_modes[i % len(payment_modes)]
            status = payment_statuses[i % len(payment_statuses)]
            
            # Check if payment already exists for this booking
            if Payment.objects.filter(booking=booking).exists():
                continue
                
            payment_data = {
                'booking': booking,
                'amount': 1500 + (i * 100),  # Varying amounts
                'mode': mode,
                'status': status,
                'transaction_id': f"{mode.upper()}{uuid.uuid4().hex[:8]}",
                'ip_address': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Test Browser)',
            }
            
            # Add mode-specific data
            if mode in ['googlepay', 'phonepe', 'paytm']:
                payment_data['upi_id'] = f'test{i}@{mode}'
            elif mode in ['debitcard', 'creditcard']:
                payment_data['card_last_four'] = f'{1234 + i:04d}'
                payment_data['card_type'] = 'Visa' if i % 2 == 0 else 'MasterCard'
            elif mode == 'paylater':
                payment_data['due_date'] = timezone.now() + timedelta(days=30)
                payment_data['repayment_terms'] = "Payment due within 30 days. No interest for first 15 days."
            
            if status == 'completed':
                payment_data['paid_at'] = timezone.now() - timedelta(hours=i)
            
            payment = Payment.objects.create(**payment_data)
            self.stdout.write(
                self.style.SUCCESS(f'Created payment {payment.id} for booking {booking.id}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created sample payment data!')
        )
