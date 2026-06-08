from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Review
from .models import ServiceProvider

@receiver(post_save, sender=Review)
def update_provider_rating(sender, instance, **kwargs):

    provider = instance.booking.provider

    avg_rating = Review.objects.filter(
        booking__provider=provider
    ).aggregate(
        Avg('rating')
    )['rating__avg']

    provider.rating = round(avg_rating, 1)

    provider.save()