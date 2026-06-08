from django.core.management.base import BaseCommand
from core.models import VegDish, NonVegDish

class Command(BaseCommand):
    help = 'Adds sample dishes to the database'

    def handle(self, *args, **kwargs):
        # Clear existing dishes
        VegDish.objects.all().delete()
        NonVegDish.objects.all().delete()

        # Add Vegetarian Dishes - Chapati + Curry
        VegDish.objects.create(
            name='Dal Makhani with Chapati',
            dish_type='chapati_curry',
            description='Creamy black lentils served with soft butter chapatis',
            price=180.00,
            is_available=True
        )

        VegDish.objects.create(
            name='Paneer Butter Masala with Chapati',
            dish_type='chapati_curry',
            description='Rich and creamy paneer curry with soft butter chapatis',
            price=220.00,
            is_available=True
        )

        VegDish.objects.create(
            name='Mix Veg Curry with Chapati',
            dish_type='chapati_curry',
            description='Assorted vegetables in a flavorful gravy with chapatis',
            price=160.00,
            is_available=True
        )

        # Add Vegetarian Dishes - Paratha
        VegDish.objects.create(
            name='Aloo Paratha',
            dish_type='paratha',
            description='Whole wheat flatbread stuffed with spiced potatoes',
            price=80.00,
            is_available=True
        )

        VegDish.objects.create(
            name='Paneer Paratha',
            dish_type='paratha',
            description='Whole wheat flatbread stuffed with spiced cottage cheese',
            price=100.00,
            is_available=True
        )

        VegDish.objects.create(
            name='Mix Veg Paratha',
            dish_type='paratha',
            description='Whole wheat flatbread stuffed with mixed vegetables',
            price=90.00,
            is_available=True
        )

        # Add Non-Vegetarian Dishes
        NonVegDish.objects.create(
            name='Butter Chicken',
            description='Tender chicken pieces in rich tomato and butter gravy',
            price=280.00,
            is_available=True
        )

        NonVegDish.objects.create(
            name='Chicken Biryani',
            description='Fragrant rice cooked with tender chicken and aromatic spices',
            price=250.00,
            is_available=True
        )

        NonVegDish.objects.create(
            name='Mutton Curry',
            description='Tender mutton pieces cooked in a spicy gravy',
            price=320.00,
            is_available=True
        )

        NonVegDish.objects.create(
            name='Fish Curry',
            description='Fresh fish cooked in a tangy and spicy curry',
            price=260.00,
            is_available=True
        )

        self.stdout.write(self.style.SUCCESS('Successfully added sample dishes')) 