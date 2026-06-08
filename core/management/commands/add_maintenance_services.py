from django.core.management.base import BaseCommand
from core.models import Service

class Command(BaseCommand):
    help = 'Add detailed maintenance & repairs services to the database.'

    def handle(self, *args, **options):
        Service.objects.filter(service_type='maintenance').delete()
        services = [
            {
                'name': 'Plumbing',
                'service_type': 'maintenance',
                'maintenance_option': 'plumbing',
                'description': 'Professional plumbing repairs, leak fixes, pipe replacements, and unclogging services.',
                'base_price': 120,
                'duration_hours': 2,
                'includes': 'Leak repair, pipe replacement, faucet installation, drain unclogging',
                'price_per_hour': 60,
            },
            {
                'name': 'Electrical Work',
                'service_type': 'maintenance',
                'maintenance_option': 'electrical',
                'description': 'Certified electricians for wiring, lighting, switchboard, and power outlet repairs.',
                'base_price': 150,
                'duration_hours': 2,
                'includes': 'Wiring, lighting installation, switchboard repair, power outlet fixes',
                'price_per_hour': 75,
            },
            {
                'name': 'Appliance Repairs',
                'service_type': 'maintenance',
                'maintenance_option': 'appliance',
                'description': 'Repair and maintenance for home appliances including washing machines, refrigerators, and ovens.',
                'base_price': 100,
                'duration_hours': 1.5,
                'includes': 'Washing machine, refrigerator, oven, microwave repairs',
                'price_per_hour': 65,
            },
            {
                'name': 'Handyman Services',
                'service_type': 'maintenance',
                'maintenance_option': 'handyman',
                'description': 'General repairs, furniture assembly, and minor home fixes by skilled handymen.',
                'base_price': 80,
                'duration_hours': 2,
                'includes': 'Furniture assembly, minor repairs, shelf installation, curtain rod fitting',
                'price_per_hour': 40,
            },
            {
                'name': 'Roof & Gutter Repairs',
                'service_type': 'maintenance',
                'maintenance_option': 'roof',
                'description': 'Inspection, cleaning, and repair of roofs and gutters to prevent leaks and water damage.',
                'base_price': 200,
                'duration_hours': 3,
                'includes': 'Roof inspection, gutter cleaning, leak repair, shingle replacement',
                'price_per_hour': 90,
            },
            {
                'name': 'Door & Window Repairs',
                'service_type': 'maintenance',
                'maintenance_option': 'door & window',
                'description': 'Repair and replacement of doors, windows, locks, and hinges for security and insulation.',
                'base_price': 110,
                'duration_hours': 1.5,
                'includes': 'Lock replacement, hinge repair, window glass replacement, door alignment',
                'price_per_hour': 55,
            },
        ]
        for s in services:
            Service.objects.create(**s)
        self.stdout.write(self.style.SUCCESS('Successfully added detailed maintenance & repairs services.')) 