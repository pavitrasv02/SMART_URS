from django.core.management.base import BaseCommand
from core.models import MenuItem

class Command(BaseCommand):
    help = 'Adds all dishes from Order Food page to MenuItem model'

    def handle(self, *args, **kwargs):
        # Clear existing menu items
        MenuItem.objects.all().delete()

        # Vegetarian Dishes
        veg_dishes = [
            # Flatbreads
            {'name': 'Roti', 'price': 15.00, 'cooking_type': 'veg'},
            {'name': 'Chapati', 'price': 15.00, 'cooking_type': 'veg'},
            {'name': 'Paratha', 'price': 30.00, 'cooking_type': 'veg'},
            {'name': 'Naan', 'price': 40.00, 'cooking_type': 'veg'},
            {'name': 'Phulka', 'price': 15.00, 'cooking_type': 'veg'},
            {'name': 'Kulcha', 'price': 35.00, 'cooking_type': 'veg'},
            {'name': 'Tandoori Roti', 'price': 45.00, 'cooking_type': 'veg'},
            {'name': 'Thepla', 'price': 25.00, 'cooking_type': 'veg'},
            
            # Curries
            {'name': 'Paneer Butter Masala', 'price': 250.00, 'cooking_type': 'veg'},
            {'name': 'Chana Masala', 'price': 180.00, 'cooking_type': 'veg'},
            {'name': 'Aloo Gobi', 'price': 160.00, 'cooking_type': 'veg'},
            {'name': 'Baingan Bharta', 'price': 170.00, 'cooking_type': 'veg'},
            {'name': 'Dal Tadka', 'price': 150.00, 'cooking_type': 'veg'},
            {'name': 'Malai Kofta', 'price': 280.00, 'cooking_type': 'veg'},
            {'name': 'Palak Paneer', 'price': 260.00, 'cooking_type': 'veg'},
            {'name': 'Vegetable Korma', 'price': 220.00, 'cooking_type': 'veg'},
            
            # Rice Items
            {'name': 'Biryani', 'price': 200.00, 'cooking_type': 'veg'},
            {'name': 'Pulao (Pilaf)', 'price': 150.00, 'cooking_type': 'veg'},
            {'name': 'Jeera Rice', 'price': 120.00, 'cooking_type': 'veg'},
            {'name': 'Lemon Rice', 'price': 130.00, 'cooking_type': 'veg'},
            {'name': 'Khichdi', 'price': 140.00, 'cooking_type': 'veg'},
            {'name': 'Fried Rice', 'price': 160.00, 'cooking_type': 'veg'},
            {'name': 'Curd Rice', 'price': 120.00, 'cooking_type': 'veg'},
            {'name': 'Tamarind Rice', 'price': 130.00, 'cooking_type': 'veg'},
            {'name': 'Steamed Rice', 'price': 100.00, 'cooking_type': 'veg'},
            {'name': 'Saffron Rice', 'price': 180.00, 'cooking_type': 'veg'},
            {'name': 'Coconut Rice', 'price': 150.00, 'cooking_type': 'veg'},
            {'name': 'Vegetable Rice', 'price': 160.00, 'cooking_type': 'veg'},
        ]

        # Non-Vegetarian Dishes
        nonveg_dishes = [
            # Flatbreads (same as veg for now)
            {'name': 'Roti', 'price': 15.00, 'cooking_type': 'nonveg'},
            {'name': 'Chapati', 'price': 15.00, 'cooking_type': 'nonveg'},
            {'name': 'Paratha', 'price': 30.00, 'cooking_type': 'nonveg'},
            {'name': 'Naan', 'price': 40.00, 'cooking_type': 'nonveg'},
            {'name': 'Phulka', 'price': 15.00, 'cooking_type': 'nonveg'},
            {'name': 'Kulcha', 'price': 35.00, 'cooking_type': 'nonveg'},
            {'name': 'Tandoori Roti', 'price': 45.00, 'cooking_type': 'nonveg'},
            {'name': 'Thepla', 'price': 25.00, 'cooking_type': 'nonveg'},
            
            # Curries
            {'name': 'Butter Chicken', 'price': 350.00, 'cooking_type': 'nonveg'},
            {'name': 'Chicken Curry', 'price': 280.00, 'cooking_type': 'nonveg'},
            {'name': 'Egg Curry', 'price': 200.00, 'cooking_type': 'nonveg'},
            {'name': 'Fish Curry', 'price': 300.00, 'cooking_type': 'nonveg'},
            {'name': 'Chicken Do Pyaza', 'price': 290.00, 'cooking_type': 'nonveg'},
            {'name': 'Chicken Chettinad', 'price': 320.00, 'cooking_type': 'nonveg'},
            {'name': 'Goan Fish Curry', 'price': 310.00, 'cooking_type': 'nonveg'},
            {'name': 'Prawn Masala', 'price': 380.00, 'cooking_type': 'nonveg'},
            
            # Rice Items
            {'name': 'Chicken Biryani', 'price': 280.00, 'cooking_type': 'nonveg'},
            {'name': 'Egg Fried Rice', 'price': 180.00, 'cooking_type': 'nonveg'},
            {'name': 'Fish Pulao', 'price': 250.00, 'cooking_type': 'nonveg'},
            {'name': 'Prawn Biryani', 'price': 350.00, 'cooking_type': 'nonveg'},
            {'name': 'Keema Rice', 'price': 220.00, 'cooking_type': 'nonveg'},
            {'name': 'Chicken Pulao', 'price': 200.00, 'cooking_type': 'nonveg'},
            {'name': 'Mutton Biryani', 'price': 320.00, 'cooking_type': 'nonveg'},
            {'name': 'Egg Pulao', 'price': 180.00, 'cooking_type': 'nonveg'},
        ]

        # Create all menu items
        for dish in veg_dishes + nonveg_dishes:
            MenuItem.objects.create(**dish)

        self.stdout.write(self.style.SUCCESS('Successfully added all dishes to MenuItem model')) 