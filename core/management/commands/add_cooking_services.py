from django.core.management.base import BaseCommand
from core.models import Service

class Command(BaseCommand):
    help = 'Add detailed cooking services to the database.'

    def handle(self, *args, **options):
        Service.objects.filter(service_type='cooking').delete()
        services = [
            {
                'name': 'Personal Chef at Home',
                'service_type': 'cooking',
                'cooking_option': 'veg',
                'description': 'Hire a professional chef to cook personalized meals in your home, tailored to your preferences and dietary needs.',
                'base_price': 200,
                'duration_hours': 4,
                'includes': 'Menu planning, grocery shopping, meal preparation, table service, kitchen cleanup',
                'price_per_hour': 50,
            },
            {
                'name': 'Daily Home Cook',
                'service_type': 'cooking',
                'cooking_option': 'veg',
                'description': 'A daily cook for regular home-cooked meals, breakfast, lunch, and dinner.',
                'base_price': 80,
                'duration_hours': 3,
                'includes': 'Meal planning, daily cooking, kitchen maintenance',
                'price_per_hour': 27,
            },
            {
                'name': 'Event/Party Catering',
                'service_type': 'cooking',
                'cooking_option': 'veg',
                'description': 'Catering services for parties and events, including multi-course meals and snacks.',
                'base_price': 500,
                'duration_hours': 6,
                'includes': 'Menu customization, food preparation, serving staff, event cleanup',
                'price_per_hour': 84,
            },
            {
                'name': 'Tiffin Services (Meal Delivery)',
                'service_type': 'cooking',
                'cooking_option': 'veg',
                'description': 'Daily or weekly meal delivery service with healthy, home-style food.',
                'base_price': 60,
                'duration_hours': 1,
                'includes': 'Meal packaging, delivery, menu rotation',
                'price_per_hour': 60,
            },
            {
                'name': 'Specialty Cuisine Cooking (South Indian, North Indian, Chinese, etc.)',
                'service_type': 'cooking',
                'cooking_option': 'veg',
                'description': 'Expert chefs prepare specialty cuisines as per your request, including regional and international dishes.',
                'base_price': 150,
                'duration_hours': 2.5,
                'includes': 'Specialty ingredients, authentic recipes, custom menu',
                'price_per_hour': 60,
            },
        ]
        for s in services:
            Service.objects.create(**s)
        self.stdout.write(self.style.SUCCESS('Successfully added detailed cooking services.')) 