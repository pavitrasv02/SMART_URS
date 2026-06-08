from django.core.management.base import BaseCommand
from core.models import Service

class Command(BaseCommand):
    help = 'Add detailed home automation services to the database.'

    def handle(self, *args, **options):
        Service.objects.filter(service_type='automation').delete()
        services = [
            {
                'name': 'Lighting Automation',
                'service_type': 'automation',
                'automation_option': 'lighting',
                'description': 'Smart lighting systems with remote control, scheduling, and energy-saving features.',
                'base_price': 180,
                'duration_hours': 2,
                'includes': 'Smart bulbs, dimmers, remote control setup, scheduling',
                'price_per_hour': 90,
            },
            {
                'name': 'Climate Control',
                'service_type': 'automation',
                'automation_option': 'climate',
                'description': 'Automated thermostats and climate systems for optimal comfort and energy efficiency.',
                'base_price': 220,
                'duration_hours': 2.5,
                'includes': 'Smart thermostat installation, climate zone setup, mobile app integration',
                'price_per_hour': 88,
            },
            {
                'name': 'Security Systems',
                'service_type': 'automation',
                'automation_option': 'security',
                'description': 'Integrated smart security systems including cameras, alarms, and sensors.',
                'base_price': 300,
                'duration_hours': 3,
                'includes': 'Camera installation, alarm setup, motion sensors, remote monitoring',
                'price_per_hour': 100,
            },
            {
                'name': 'Voice Assistant Integration',
                'service_type': 'automation',
                'automation_option': 'voice',
                'description': 'Setup and integration of voice assistants for hands-free home control.',
                'base_price': 100,
                'duration_hours': 1,
                'includes': 'Amazon Alexa, Google Home, Apple HomeKit setup',
                'price_per_hour': 100,
            },
            {
                'name': 'Entertainment Systems',
                'service_type': 'automation',
                'automation_option': 'entertainment',
                'description': 'Smart home entertainment systems including audio, video, and streaming integration.',
                'base_price': 250,
                'duration_hours': 2.5,
                'includes': 'Smart TV setup, surround sound, streaming device integration',
                'price_per_hour': 100,
            },
            {
                'name': 'Energy Monitoring',
                'service_type': 'automation',
                'automation_option': 'appliances',
                'description': 'Smart energy monitoring and management for efficient power usage.',
                'base_price': 120,
                'duration_hours': 1.5,
                'includes': 'Smart meters, energy usage reports, mobile app setup',
                'price_per_hour': 80,
            },
        ]
        for s in services:
            Service.objects.create(**s)
        self.stdout.write(self.style.SUCCESS('Successfully added detailed home automation services.')) 