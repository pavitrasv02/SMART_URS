from django.db import models

# Service Type Choices
SERVICE_TYPE_CHOICES = [
    ('cleaning', 'Cleaning Services'),
    ('maintenance', 'Maintenance & Repairs'),
    ('gardening', 'Gardening & Landscaping'),
    ('automation', 'Home Automation'),
    ('security', 'Security Services'),
    ('cooking', 'Cooking Services'),
]

# Service-specific Options
CLEANING_OPTIONS = [
    ('regular', 'Regular House Cleaning'),
    ('deep', 'Deep Cleaning'),
    ('carpet', 'Carpet and Upholstery Cleaning'),
    ('window', 'Window Cleaning'),
    ('move', 'Move-in/Move-out Cleaning'),
    ('home', 'Home Cleaning'),
]

MAINTENANCE_OPTIONS = [
    ('plumbing', 'Plumbing Repairs'),
    ('electrical', 'Electrical Repairs'),
    ('carpentry', 'Carpentry Work'),
    ('painting', 'Painting Services'),
    ('appliance', 'Appliance Repair'),
    ('hvac', 'HVAC Maintenance'),
    ('roof', 'Roof Repairs'),
    ('pest', 'Pest Control'),
    ('locksmith', 'Locksmith Services'),
]

GARDENING_OPTIONS = [
    ('lawn', 'Lawn Maintenance'),
    ('garden', 'Garden Design'),
    ('irrigation', 'Irrigation Systems'),
    ('tree', 'Tree Services'),
    ('landscaping', 'Landscaping'),
    ('planting', 'Plant Installation'),
    ('mulching', 'Mulching Services'),
    ('fertilization', 'Fertilization Services'),
    ('weed_control', 'Weed Control'),
]

AUTOMATION_OPTIONS = [
    ('lighting', 'Smart Lighting'),
    ('security', 'Security Systems'),
    ('climate', 'Climate Control'),
    ('entertainment', 'Home Entertainment'),
    ('voice', 'Voice Control Systems'),
    ('door_locks', 'Smart Door Locks'),
    ('cameras', 'Smart Cameras'),
    ('speakers', 'Smart Speakers'),
    ('appliances', 'Smart Appliances'),
]

SECURITY_OPTIONS = [
    ('cctv', 'CCTV Installation'),
    ('alarm', 'Alarm Systems'),
    ('access', 'Access Control'),
    ('monitoring', '24/7 Monitoring'),
    ('consultation', 'Security Consultation'),
    ('fire_safety', 'Fire Safety Systems'),
    ('intercom', 'Intercom Systems'),
    ('biometric', 'Biometric Security'),
    ('smart_locks', 'Smart Lock Installation'),
]

COOKING_OPTIONS = [
('Daily Home Cook', 'daily_home_cook'),
('Event/Party Catering', 'event_party_catering'),
('Kids Meal Service', 'kids_meal_service'),
('Personal Chef at Home', 'personal_chef_at_home'),
('Specialty Cuisine Cooking', 'specialty_cuisine_cooking'),
('Tiffin Services', 'tiffin_services'),


]

VEG_DISH_TYPES = [
    ('chapati_curry', 'Chapati + Curry'),
    ('paratha', 'Paratha'),
    ('rice_curry', 'Rice + Curry'),
    ('thali', 'Thali'),
    ('snacks', 'Snacks'),
    ('dessert', 'Dessert'),
]


# Area Coverage Choices
AREA_COVERAGE_CHOICES = [
    ('studio', 'Studio Apartment (300-500 sq ft)'),
    ('1bhk', '1 BHK (500-800 sq ft)'),
    ('2bhk', '2 BHK (800-1200 sq ft)'),
    ('3bhk', '3 BHK (1200-1800 sq ft)'),
    ('4bhk', '4 BHK (1800-2500 sq ft)'),
    ('villa', 'Villa (2500+ sq ft)'),
    ('commercial_small', 'Small Commercial (500-1000 sq ft)'),
    ('commercial_medium', 'Medium Commercial (1000-2000 sq ft)'),
    ('commercial_large', 'Large Commercial (2000+ sq ft)'),
]

# Property Type Choices
PROPERTY_TYPE_CHOICES = [
    ('residential', 'Residential'),
    ('commercial', 'Commercial'),
    ('industrial', 'Industrial'),
    ('mixed', 'Mixed Use'),
]

# Location Type Choices
LOCATION_TYPE_CHOICES = [
    ('urban', 'Urban'),
    ('suburban', 'Suburban'),
    ('rural', 'Rural'),
]


class User(models.Model):
    name     = models.CharField(max_length=100)
    email    = models.EmailField(unique=True)
    phone    = models.CharField(max_length=15)
    password = models.CharField(max_length=100)
    address  = models.TextField()

    def __str__(self):
        return self.name


class ServiceProvider(models.Model):
    name         = models.CharField(max_length=100)
    email        = models.EmailField(unique=True)
    phone        = models.CharField(max_length=15)
    password     = models.CharField(max_length=100)
    service_type = models.CharField(max_length=100, choices=SERVICE_TYPE_CHOICES)
    location     = models.CharField(max_length=100)
    rating       = models.FloatField(default=0)

    # Service-specific fields
    cleaning_option = models.CharField(max_length=20, choices=CLEANING_OPTIONS, null=True, blank=True)
    maintenance_option = models.CharField(max_length=20, choices=MAINTENANCE_OPTIONS, null=True, blank=True)
    gardening_option = models.CharField(max_length=20, choices=GARDENING_OPTIONS, null=True, blank=True)
    automation_option = models.CharField(max_length=20, choices=AUTOMATION_OPTIONS, null=True, blank=True)
    security_option = models.CharField(max_length=20, choices=SECURITY_OPTIONS, null=True, blank=True)

    # Additional provider details
    experience_years = models.IntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    availability = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    languages = models.CharField(max_length=200, blank=True)
    working_hours = models.CharField(max_length=100, blank=True)
    service_areas = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"


class Service(models.Model):
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    image_name = models.CharField(
        max_length=100,
        default='default.jpg',
        blank=True,
        help_text='Enter image filename from static/images/services/',
    )

    # Service-specific fields
    cleaning_option = models.CharField(max_length=20, choices=CLEANING_OPTIONS, null=True, blank=True)
    maintenance_option = models.CharField(max_length=20, choices=MAINTENANCE_OPTIONS, null=True, blank=True)
    gardening_option = models.CharField(max_length=20, choices=GARDENING_OPTIONS, null=True, blank=True)
    automation_option = models.CharField(max_length=20, choices=AUTOMATION_OPTIONS, null=True, blank=True)
    security_option = models.CharField(max_length=20, choices=SECURITY_OPTIONS, null=True, blank=True)
    cooking_option = models.CharField(max_length=100, choices=COOKING_OPTIONS, null=True, blank=True)

    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE_CHOICES, null=True, blank=True)
    square_footage = models.IntegerField(null=True, blank=True, help_text="Exact square footage of the property")
    floor_count = models.IntegerField(null=True, blank=True, help_text="Number of floors in the property")
    includes = models.TextField(null=True, blank=True)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    details = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"

    @property
    def has_image(self):
        return bool(self.image_name and self.image_name.strip() and self.image_name.strip() != 'default.jpg')

    @property
    def static_image_path(self):
        filename = (self.image_name or 'default.jpg').strip() or 'default.jpg'
        return f'images/services/{filename}'


class MenuItem(models.Model):
    COOKING_TYPE_CHOICES = [
        ('veg', 'Veg'),
        ('nonveg', 'Non-Veg'),
    ]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    cooking_type = models.CharField(max_length=10, choices=COOKING_TYPE_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.cooking_type})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Provider Assigned', 'Provider Assigned'),
        ('Accepted', 'Accepted'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True)
    booking_date = models.DateField(null=True, blank=True)
    booking_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Cooking service specific fields
    dish = models.ForeignKey('VegDish', on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_as_dish')
    non_veg_dish = models.ForeignKey('NonVegDish', on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_as_non_veg_dish')
    dish_type = models.CharField(max_length=10, choices=[('veg', 'Vegetarian'), ('non_veg', 'Non-Vegetarian')], null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    special_instructions = models.TextField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    menu_items = models.ManyToManyField(MenuItem, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        provider_name = self.provider.name if self.provider else "No Provider"
        return f"Booking {self.id} – {self.user.name} with {provider_name}"


class Payment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('googlepay', 'Google Pay'),
        ('phonepe', 'PhonePe'),
        ('paytm', 'PayTM'),
        ('debitcard', 'Debit Card'),
        ('creditcard', 'Credit Card'),
        ('cod', 'Cash on Delivery'),
        ('paylater', 'Pay Later'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Wallet'),
        ('emi', 'EMI'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mode = models.CharField(max_length=50, choices=PAYMENT_MODE_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    # Additional payment details
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_gateway_response = models.TextField(blank=True, null=True)

    # Card details (for card payments) - stored securely
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    card_type = models.CharField(max_length=20, blank=True, null=True)  # Visa, MasterCard, etc.

    # UPI details
    upi_id = models.CharField(max_length=100, blank=True, null=True)

    # Pay Later details
    due_date = models.DateTimeField(blank=True, null=True)
    repayment_terms = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    # Additional metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    # Razorpay gateway fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} – ₹{self.amount} – {self.get_status_display()}"

    @property
    def user(self):
        return self.booking.user

    @property
    def service_name(self):
        if self.booking.service:
            return self.booking.service.name
        elif self.booking.dish:
            return f"{self.booking.dish.name} (Veg)"
        elif self.booking.non_veg_dish:
            return f"{self.booking.non_veg_dish.name} (Non-Veg)"
        else:
            return "Service"


class Review(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    rating  = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review {self.id} – {self.rating} stars"


class CookingService(models.Model):
    CATEGORY_CHOICES = [
        ('veg', 'Vegetarian'),
        ('non_veg', 'Non-Vegetarian'),
    ]

    CUISINE_CHOICES = [
        ('indian', 'Indian'),
        ('chinese', 'Chinese'),
        ('italian', 'Italian'),
        ('mexican', 'Mexican'),
        ('thai', 'Thai'),
        ('japanese', 'Japanese'),
        ('continental', 'Continental'),
        ('other', 'Other'),
    ]

    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snacks', 'Snacks'),
        ('all_day', 'All Day'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    # Service-specific fields
    cooking_option = models.CharField(max_length=30, choices=COOKING_OPTIONS, null=True, blank=True, help_text="Select the specific cooking service")
    cuisine_type = models.CharField(max_length=20, choices=CUISINE_CHOICES, blank=True, null=True)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, blank=True, null=True)
    preparation_time = models.IntegerField(help_text="Preparation time in minutes", blank=True, null=True)
    serving_size = models.IntegerField(help_text="Number of people this dish serves", blank=True, null=True)
    ingredients = models.TextField(help_text="Main ingredients used", blank=True, null=True)
    dietary_info = models.TextField(help_text="Dietary information (e.g., gluten-free, dairy-free)", blank=True, null=True)
    chef_speciality = models.BooleanField(default=False, help_text="Mark if this is a chef's speciality")

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

class VegDish(models.Model):
    name = models.CharField(max_length=100)
    dish_type = models.CharField(max_length=20, choices=VEG_DISH_TYPES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_dish_type_display()})"

class NonVegDish(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Bread(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ServiceRequest(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('cleaning', 'Cleaning'),
        ('maintenance', 'Maintenance'),
        ('garden', 'Garden'),
        ('home_appliance', 'Home Appliance'),
        ('security', 'Security'),
        ('food', 'Food'),
    ]

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    service_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # User Details
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()

    # Booking Details
    date = models.DateField()
    time = models.TimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Request Status
    STATUS_CHOICES = [
        ('not_done', 'Not Done'),
        ('done', 'Done'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_done')
    created_at = models.DateTimeField(auto_now_add=True)

    # Service-specific option fields
    cleaning_option = models.CharField(max_length=20, choices=CLEANING_OPTIONS, null=True, blank=True, help_text="Select the specific cleaning service")
    maintenance_option = models.CharField(max_length=20, choices=MAINTENANCE_OPTIONS, null=True, blank=True, help_text="Select the specific maintenance service")
    gardening_option = models.CharField(max_length=20, choices=GARDENING_OPTIONS, null=True, blank=True, help_text="Select the specific gardening service")
    automation_option = models.CharField(max_length=20, choices=AUTOMATION_OPTIONS, null=True, blank=True, help_text="Select the specific home automation service")
    security_option = models.CharField(max_length=20, choices=SECURITY_OPTIONS, null=True, blank=True, help_text="Select the specific security service")
    cooking_option = models.CharField(max_length=30, choices=COOKING_OPTIONS, null=True, blank=True, help_text="Select the specific cooking service")

    # Service-specific fields for Cleaning
    area_size = models.CharField(max_length=50, blank=True, null=True, help_text="Size of the area to be cleaned (e.g., 1000 sq ft)")
    cleaning_frequency = models.CharField(max_length=50, blank=True, null=True, help_text="How often the cleaning service is needed")
    special_requirements = models.TextField(blank=True, null=True, help_text="Any special cleaning requirements")

    # Service-specific fields for Maintenance
    maintenance_type = models.CharField(max_length=50, blank=True, null=True, help_text="Type of maintenance required")
    equipment_age = models.CharField(max_length=50, blank=True, null=True, help_text="Age of the equipment needing maintenance")
    urgency_level = models.CharField(max_length=20, blank=True, null=True, help_text="Urgency level of the maintenance request")

    # Service-specific fields for Garden
    garden_size = models.CharField(max_length=50, blank=True, null=True, help_text="Size of the garden")
    service_frequency = models.CharField(max_length=50, blank=True, null=True, help_text="How often the garden service is needed")
    garden_type = models.CharField(max_length=50, blank=True, null=True, help_text="Type of garden (e.g., vegetable, flower, lawn)")

    # Service-specific fields for Home Appliance
    appliance_type = models.CharField(max_length=50, blank=True, null=True, help_text="Type of appliance needing service")
    brand = models.CharField(max_length=50, blank=True, null=True, help_text="Brand of the appliance")
    model = models.CharField(max_length=50, blank=True, null=True, help_text="Model of the appliance")
    issue_description = models.TextField(blank=True, null=True, help_text="Detailed description of the issue")

    # Service-specific fields for Security
    security_system_type = models.CharField(max_length=50, blank=True, null=True, help_text="Type of security system")
    property_size = models.CharField(max_length=50, blank=True, null=True, help_text="Size of the property")
    existing_equipment = models.TextField(blank=True, null=True, help_text="Existing security equipment")

    # Service-specific fields for Food
    meal_type = models.CharField(max_length=50, blank=True, null=True, help_text="Type of meal (e.g., breakfast, lunch, dinner)")
    cuisine = models.CharField(max_length=50, blank=True, null=True, help_text="Preferred cuisine")
    dietary_restrictions = models.TextField(blank=True, null=True, help_text="Any dietary restrictions")
    number_of_people = models.IntegerField(blank=True, null=True, help_text="Number of people to be served")

    def __str__(self):
        return f"{self.service_name} - {self.name}"

    def get_service_type_display(self):
        return dict(self.SERVICE_TYPE_CHOICES).get(self.service_type, self.service_type)


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('booking_created', 'Booking Created'),
        ('provider_assigned', 'Provider Assigned'),
        ('booking_accepted', 'Booking Accepted'),
        ('booking_cancelled', 'Booking Cancelled'),
        ('service_completed', 'Service Completed'),
        ('new_message', 'New Chat Message'),
        ('review_received', 'Review Received'),
        ('service_reminder', 'Service Reminder'),
        ('review_reminder', 'Review Reminder'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='booking_created')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ChatRoom(models.Model):
    """Private chat room tied to a single accepted booking."""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='chat_room')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat — Booking #{self.booking_id}"


class ChatMessage(models.Model):
    SENDER_TYPES = [
        ('customer', 'Customer'),
        ('provider', 'Provider'),
    ]

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPES)
    sender_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sender_provider = models.ForeignKey(ServiceProvider, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender_type}: {self.content[:40]}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'service')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.name} ♥ {self.service.name}"


class ProviderTimeSlot(models.Model):
    SLOT_STATUS = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('unavailable', 'Unavailable'),
    ]
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=SLOT_STATUS, default='available')

    class Meta:
        unique_together = ('provider', 'date', 'time')
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.provider.name} — {self.date} {self.time} ({self.status})"


class Invoice(models.Model):
    """Auto-generated when a booking is completed."""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=30, unique=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_number
