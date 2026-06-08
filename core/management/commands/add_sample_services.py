from django.core.management.base import BaseCommand
from core.models import Service

class Command(BaseCommand):
    help = 'Adds sample services to the database'

    def handle(self, *args, **kwargs):
        # Sample services for all types
        all_services = [
            # Cleaning Services
            {
                'name': 'Regular House Cleaning',
                'service_type': 'cleaning',
                'cleaning_option': 'regular',
                'description': 'Complete house cleaning service including dusting, vacuuming, and bathroom cleaning',
                'base_price': 50.00,
                'duration_hours': 3,
                'area_coverage': 'medium',
                'property_type': 'apartment',
                'includes': 'Dusting Vacuuming Bathroom-Cleaning Kitchen-Cleaning'
            },
            {
                'name': 'Deep Cleaning Service',
                'service_type': 'cleaning',
                'cleaning_option': 'deep',
                'description': 'Thorough deep cleaning of your entire home including hard-to-reach areas',
                'base_price': 100.00,
                'duration_hours': 6,
                'area_coverage': 'large',
                'property_type': 'house',
                'includes': 'Deep-Cleaning Window-Cleaning Carpet-Cleaning Appliance-Cleaning'
            },
            {
                'name': 'Move In/Out Cleaning',
                'service_type': 'cleaning',
                'cleaning_option': 'move',
                'description': 'Complete cleaning service for moving in or out of a property',
                'base_price': 150.00,
                'duration_hours': 8,
                'area_coverage': 'large',
                'property_type': 'any',
                'includes': 'Deep-Cleaning Wall-Cleaning Cabinet-Cleaning Floor-Cleaning'
            },
            
            # Maintenance Services
            {
                'name': 'Plumbing Repair',
                'service_type': 'maintenance',
                'maintenance_option': 'plumbing',
                'description': 'Professional plumbing repair and maintenance services',
                'base_price': 75.00,
                'duration_hours': 2,
                'property_type': 'any',
                'includes': 'Leak-Repair Pipe-Installation Faucet-Repair Drain-Cleaning'
            },
            {
                'name': 'Electrical Repair',
                'service_type': 'maintenance',
                'maintenance_option': 'electrical',
                'description': 'Expert electrical repair and installation services',
                'base_price': 85.00,
                'duration_hours': 3,
                'property_type': 'any',
                'includes': 'Wiring-Repair Outlet-Installation Circuit-Repair Light-Fixture-Installation'
            },
            {
                'name': 'HVAC Maintenance',
                'service_type': 'maintenance',
                'maintenance_option': 'hvac',
                'description': 'Complete HVAC system maintenance and repair',
                'base_price': 120.00,
                'duration_hours': 4,
                'property_type': 'any',
                'includes': 'System-Cleaning Filter-Replacement Duct-Cleaning Thermostat-Installation'
            },
            
            # Gardening Services
            {
                'name': 'Lawn Maintenance',
                'service_type': 'gardening',
                'gardening_option': 'lawn',
                'description': 'Regular lawn care and maintenance services',
                'base_price': 60.00,
                'duration_hours': 3,
                'area_coverage': 'medium',
                'property_type': 'house',
                'includes': 'Mowing Edging Fertilizing Weed-Control'
            },
            {
                'name': 'Garden Design',
                'service_type': 'gardening',
                'gardening_option': 'design',
                'description': 'Professional garden design and landscaping services',
                'base_price': 200.00,
                'duration_hours': 8,
                'area_coverage': 'large',
                'property_type': 'house',
                'includes': 'Design-Planning Plant-Selection Layout-Installation Irrigation-Setup'
            },
            {
                'name': 'Tree Care',
                'service_type': 'gardening',
                'gardening_option': 'tree',
                'description': 'Expert tree maintenance and care services',
                'base_price': 150.00,
                'duration_hours': 4,
                'property_type': 'any',
                'includes': 'Pruning Trimming Disease-Treatment Tree-Removal'
            },
            
            # Automation Services
            {
                'name': 'Smart Home Setup',
                'service_type': 'automation',
                'automation_option': 'smart_home',
                'description': 'Complete smart home system installation and setup',
                'base_price': 300.00,
                'duration_hours': 6,
                'property_type': 'any',
                'includes': 'Hub-Installation Device-Setup App-Configuration Voice-Control-Setup'
            },
            {
                'name': 'Security Camera Installation',
                'service_type': 'automation',
                'automation_option': 'security_cameras',
                'description': 'Professional security camera system installation',
                'base_price': 250.00,
                'duration_hours': 5,
                'property_type': 'any',
                'includes': 'Camera-Installation DVR-Setup Mobile-App-Setup Remote-Monitoring-Setup'
            },
            {
                'name': 'Home Theater Setup',
                'service_type': 'automation',
                'automation_option': 'home_theater',
                'description': 'Complete home theater system installation and calibration',
                'base_price': 400.00,
                'duration_hours': 8,
                'property_type': 'any',
                'includes': 'Speaker-Installation Screen-Setup Sound-Calibration Remote-Programming'
            },
            
            # Security Services
            {
                'name': 'Alarm System Installation',
                'service_type': 'security',
                'security_option': 'alarm',
                'description': 'Professional security alarm system installation',
                'base_price': 350.00,
                'duration_hours': 6,
                'property_type': 'any',
                'includes': 'System-Installation Sensor-Setup Control-Panel-Setup Mobile-App-Setup'
            },
            {
                'name': 'Access Control Setup',
                'service_type': 'security',
                'security_option': 'access_control',
                'description': 'Complete access control system installation',
                'base_price': 450.00,
                'duration_hours': 8,
                'property_type': 'any',
                'includes': 'Lock-Installation Keypad-Setup Card-System-Setup Mobile-Access-Setup'
            },
            {
                'name': 'Security Assessment',
                'service_type': 'security',
                'security_option': 'assessment',
                'description': 'Comprehensive home security assessment and recommendations',
                'base_price': 200.00,
                'duration_hours': 4,
                'property_type': 'any',
                'includes': 'Vulnerability-Assessment Security-Recommendations Implementation-Plan'
            },

            # Cooking Services
            {
                'name': 'Daily Meal Preparation',
                'service_type': 'cooking',
                'cooking_option': 'daily',
                'description': 'Professional chef for daily meal preparation and cooking',
                'base_price': 80.00,
                'duration_hours': 4,
                'property_type': 'any',
                'includes': 'Meal-Planning Grocery-Shopping Cooking Meal-Packaging'
            },
            {
                'name': 'Party Catering',
                'service_type': 'cooking',
                'cooking_option': 'party',
                'description': 'Complete catering service for parties and events',
                'base_price': 500.00,
                'duration_hours': 8,
                'property_type': 'any',
                'includes': 'Menu-Planning Food-Preparation Service Cleanup'
            },
            {
                'name': 'Cooking Classes',
                'service_type': 'cooking',
                'cooking_option': 'classes',
                'description': 'Personal cooking lessons and culinary training',
                'base_price': 150.00,
                'duration_hours': 3,
                'property_type': 'any',
                'includes': 'Recipe-Instruction Technique-Demonstration Hands-on-Training'
            },
            {
                'name': 'Special Diet Cooking',
                'service_type': 'cooking',
                'cooking_option': 'special_diet',
                'description': 'Specialized cooking for dietary restrictions and preferences',
                'base_price': 100.00,
                'duration_hours': 4,
                'property_type': 'any',
                'includes': 'Diet-Planning Special-Ingredients Meal-Preparation Nutrition-Guidance'
            },
            {
                'name': 'Meal Prep Service',
                'service_type': 'cooking',
                'cooking_option': 'meal_prep',
                'description': 'Weekly meal preparation and planning service',
                'base_price': 200.00,
                'duration_hours': 6,
                'property_type': 'any',
                'includes': 'Weekly-Planning Bulk-Cooking Portioning Storage-Setup'
            }
        ]

        # Create all services
        for service_data in all_services:
            Service.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created service "{service_data["name"]}"')
            ) 