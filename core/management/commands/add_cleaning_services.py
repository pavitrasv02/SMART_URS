from django.core.management.base import BaseCommand
from core.models import Service

class Command(BaseCommand):
    help = 'Adds cleaning services to the database'

    def handle(self, *args, **kwargs):
        # Clear existing cleaning services
        Service.objects.filter(service_type='cleaning').delete()

        # Regular House Cleaning
        Service.objects.create(
            name='Regular House Cleaning',
            service_type='cleaning',
            cleaning_option='regular',
            description='Standard cleaning service including dusting, vacuuming, mopping, and bathroom cleaning.',
            base_price=150.00,
            duration_hours=3.0,
            includes='Dusting, Vacuuming, Mopping, Bathroom Cleaning, Kitchen Cleaning',
            price_per_hour=50.00
        )

        # Deep Cleaning
        Service.objects.create(
            name='Deep Cleaning Service',
            service_type='cleaning',
            cleaning_option='deep',
            description='Thorough cleaning service including all regular cleaning tasks plus deep cleaning of hard-to-reach areas.',
            base_price=300.00,
            duration_hours=6.0,
            includes='All Regular Cleaning Tasks, Deep Cleaning of Hard-to-Reach Areas, Inside Cabinets, Behind Appliances',
            price_per_hour=50.00
        )

        # Carpet and Upholstery Cleaning
        Service.objects.create(
            name='Carpet & Upholstery Cleaning',
            service_type='cleaning',
            cleaning_option='carpet',
            description='Professional cleaning of carpets, rugs, and upholstered furniture.',
            base_price=200.00,
            duration_hours=4.0,
            includes='Carpet Cleaning, Rug Cleaning, Upholstery Cleaning, Stain Removal',
            price_per_hour=50.00
        )

        # Window Cleaning
        Service.objects.create(
            name='Window Cleaning Service',
            service_type='cleaning',
            cleaning_option='window',
            description='Professional cleaning of windows, glass doors, and mirrors.',
            base_price=180.00,
            duration_hours=3.0,
            includes='Window Cleaning, Glass Door Cleaning, Mirror Cleaning, Window Frame Cleaning',
            price_per_hour=60.00
        )

        # Move-in/Move-out Cleaning
        Service.objects.create(
            name='Move-in/Move-out Cleaning',
            service_type='cleaning',
            cleaning_option='move',
            description='Comprehensive cleaning service for properties before moving in or after moving out.',
            base_price=400.00,
            duration_hours=8.0,
            includes='Deep Cleaning of All Areas, Appliance Cleaning, Cabinet Cleaning, Floor Cleaning',
            price_per_hour=50.00
        )

        self.stdout.write(self.style.SUCCESS('Successfully added cleaning services')) 