from django.db import migrations

def add_sample_dishes(apps, schema_editor):
    VegDish = apps.get_model('core', 'VegDish')
    NonVegDish = apps.get_model('core', 'NonVegDish')

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

def remove_sample_dishes(apps, schema_editor):
    VegDish = apps.get_model('core', 'VegDish')
    NonVegDish = apps.get_model('core', 'NonVegDish')
    VegDish.objects.all().delete()
    NonVegDish.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_sample_dishes, remove_sample_dishes),
    ] 