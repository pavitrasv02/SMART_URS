from django.core.management.base import BaseCommand
from core.models import Service

class Command(BaseCommand):
    help = 'Adds security services to the database'

    def handle(self, *args, **kwargs):
        # Clear existing security services
        Service.objects.filter(service_type='security').delete()

        # CCTV Installation
        Service.objects.create(
            name='CCTV Installation',
            service_type='security',
            security_option='cctv',
            description='Professional CCTV system installation and setup.',
            base_price=400.00,
            duration_hours=5.0,
            includes='Camera Installation, DVR Setup, Mobile App Configuration, Testing',
            price_per_hour=80.00
        )

        # Alarm Systems
        Service.objects.create(
            name='Alarm System Installation',
            service_type='security',
            security_option='alarm',
            description='Professional security alarm system installation.',
            base_price=350.00,
            duration_hours=4.0,
            includes='Alarm Installation, Sensor Setup, Control Panel Configuration, Testing',
            price_per_hour=87.50
        )

        # Access Control
        Service.objects.create(
            name='Access Control Systems',
            service_type='security',
            security_option='access',
            description='Professional access control system installation.',
            base_price=500.00,
            duration_hours=6.0,
            includes='System Installation, Card Reader Setup, Access Control Configuration',
            price_per_hour=83.33
        )

        # 24/7 Monitoring
        Service.objects.create(
            name='24/7 Security Monitoring',
            service_type='security',
            security_option='monitoring',
            description='Professional security monitoring service setup.',
            base_price=200.00,
            duration_hours=2.0,
            includes='Monitoring Setup, Emergency Response Configuration, Testing',
            price_per_hour=100.00
        )

        # Security Consultation
        Service.objects.create(
            name='Security Consultation',
            service_type='security',
            security_option='consultation',
            description='Professional security assessment and consultation.',
            base_price=250.00,
            duration_hours=3.0,
            includes='Security Assessment, Risk Analysis, Recommendations, Implementation Plan',
            price_per_hour=83.33
        )

        # Fire Safety Systems
        Service.objects.create(
            name='Fire Safety Systems',
            service_type='security',
            security_option='fire_safety',
            description='Professional fire safety system installation.',
            base_price=450.00,
            duration_hours=5.0,
            includes='Smoke Detector Installation, Fire Alarm Setup, Emergency Lighting',
            price_per_hour=90.00
        )

        # Intercom Systems
        Service.objects.create(
            name='Intercom System Installation',
            service_type='security',
            security_option='intercom',
            description='Professional intercom system installation.',
            base_price=300.00,
            duration_hours=4.0,
            includes='Intercom Installation, Wiring, Testing, Configuration',
            price_per_hour=75.00
        )

        # Biometric Security
        Service.objects.create(
            name='Biometric Security Systems',
            service_type='security',
            security_option='biometric',
            description='Professional biometric security system installation.',
            base_price=600.00,
            duration_hours=6.0,
            includes='Biometric Device Installation, Database Setup, User Enrollment',
            price_per_hour=100.00
        )

        # Smart Lock Installation
        Service.objects.create(
            name='Smart Lock Security',
            service_type='security',
            security_option='smart_locks',
            description='Professional smart lock security system installation.',
            base_price=250.00,
            duration_hours=2.0,
            includes='Smart Lock Installation, App Setup, Access Code Configuration',
            price_per_hour=125.00
        )

        self.stdout.write(self.style.SUCCESS('Successfully added security services')) 