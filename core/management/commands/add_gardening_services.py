from django.core.management.base import BaseCommand
from core.models import Service

class Command(BaseCommand):
    help = 'Add detailed gardening & landscaping services to the database.'

    def handle(self, *args, **options):
        Service.objects.filter(service_type='gardening').delete()
        services = [
            {
                'name': 'Lawn Care',
                'service_type': 'gardening',
                'gardening_option': 'lawn',
                'description': 'Regular mowing, edging, fertilizing, and weed control for a healthy, green lawn.',
                'base_price': 90,
                'duration_hours': 1.5,
                'includes': 'Mowing, edging, fertilizing, weed control',
                'price_per_hour': 60,
            },
            {
                'name': 'Garden Maintenance',
                'service_type': 'gardening',
                'gardening_option': 'garden',
                'description': 'Ongoing care for flower beds, shrubs, and plants including pruning and mulching.',
                'base_price': 100,
                'duration_hours': 2,
                'includes': 'Pruning, mulching, deadheading, plant health checks',
                'price_per_hour': 50,
            },
            {
                'name': 'Landscaping Design',
                'service_type': 'gardening',
                'gardening_option': 'landscaping',
                'description': 'Custom landscape design and installation to enhance your outdoor space.',
                'base_price': 300,
                'duration_hours': 4,
                'includes': 'Design consultation, plant selection, installation',
                'price_per_hour': 100,
            },
            {
                'name': 'Irrigation Systems',
                'service_type': 'gardening',
                'gardening_option': 'irrigation',
                'description': 'Installation and maintenance of efficient irrigation and sprinkler systems.',
                'base_price': 180,
                'duration_hours': 2.5,
                'includes': 'Sprinkler installation, drip irrigation, repairs',
                'price_per_hour': 72,
            },
            {
                'name': 'Tree Services',
                'service_type': 'gardening',
                'gardening_option': 'tree',
                'description': 'Tree trimming, pruning, removal, and health assessments by certified arborists.',
                'base_price': 250,
                'duration_hours': 3,
                'includes': 'Trimming, pruning, removal, health assessment',
                'price_per_hour': 90,
            },
            {
                'name': 'Outdoor Enhancements',
                'service_type': 'gardening',
                'gardening_option': 'mulching',
                'description': 'Installation of garden lighting, water features, and decorative elements.',
                'base_price': 200,
                'duration_hours': 2,
                'includes': 'Garden lighting, water features, decorative stones',
                'price_per_hour': 100,
            },
        ]
        for s in services:
            Service.objects.create(**s)
        self.stdout.write(self.style.SUCCESS('Successfully added detailed gardening & landscaping services.')) 