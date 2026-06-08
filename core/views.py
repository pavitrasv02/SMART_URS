from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count, Prefetch, Q, Sum
from django.db.models.functions import ExtractHour, TruncMonth
from django.contrib.admin.views.decorators import staff_member_required
import json
from decimal import Decimal
from collections import defaultdict
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import timedelta, datetime
from django.http import HttpResponse
from django.contrib.auth.models import User as AuthUser
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


def get_custom_user_from_request(request):
    """Resolve the app's custom User from session or authenticated request user."""
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            request.session.pop('user_id', None)

    if hasattr(request, 'user') and request.user.is_authenticated:
        return User.objects.filter(email=request.user.email).first()

    return None


def create_admin(request):
    if not AuthUser.objects.filter(username="admin").exists():
        AuthUser.objects.create_superuser(
            username="admin",
            email="admin@gmail.com",
            password="admin123"
        )
        return HttpResponse("Superuser created!")
    else:
        return HttpResponse("Superuser already exists!")


from .models import (
    User, ServiceProvider, Service, Booking,
    Payment, Review, CookingService, VegDish, NonVegDish,
    SERVICE_TYPE_CHOICES, MenuItem, Bread, ServiceRequest,
    Notification, Favorite, ProviderTimeSlot,
)
from .marketplace_utils import (
    get_available_slots,
    assign_provider_for_slot,
    mark_slot_occupied,
)
from .tasks import (
    send_booking_confirmation_email,
    dispatch_notification_task,
    schedule_booking_reminders,
    send_review_reminder_task,
)


recommendations = []


def home(request):
    recommendations = []
    # Get all services and organize them by type
    services = Service.objects.all().order_by('service_type', 'name')
    services_by_type = {}

    for service in services:
        if service.service_type not in services_by_type:
            services_by_type[service.service_type] = []
        services_by_type[service.service_type].append(service)

    providers = None
    if request.method == 'POST':
        service_type = request.POST.get('service_type')
        location = request.POST.get('location')

        filter_kwargs = {}
        if service_type:
            filter_kwargs['service_type__icontains'] = service_type
        if location:
            filter_kwargs['location__icontains'] = location

        if filter_kwargs:
            providers = ServiceProvider.objects.filter(**filter_kwargs)
        else:
            providers = ServiceProvider.objects.all()
    user_id = request.session.get('user_id')

    if user_id:
        try:
            user = User.objects.get(id=user_id)

            last_booking = Booking.objects.filter(
                user=user
            ).order_by('-id').first()

            if last_booking and last_booking.service:
                recommendations = Service.objects.filter(
                    service_type=last_booking.service.service_type
                ).exclude(
                    id=last_booking.service.id
                )[:4]

        except User.DoesNotExist:
            pass

    favorite_ids = set()
    if user_id:
        favorite_ids = set(
            Favorite.objects.filter(user_id=user_id).values_list('service_id', flat=True)
        )

    context = {
        'services': services,
        'services_by_type': services_by_type,
        'providers': providers,
        'service_types': dict(SERVICE_TYPE_CHOICES),
        'recommendations': recommendations,
        'favorite_ids': favorite_ids,
    }
    return render(request, 'home.html', context)


def signup(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        pw = request.POST['password']
        pw2 = request.POST['confirm_password']
        if pw != pw2:
            return render(request, 'signup.html', {'error': 'Passwords do not match.'})
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error': 'Email already registered.'})
        user = User.objects.create(name=name, email=email, phone=phone, password=pw, address=address)
        request.session['user_id'] = user.id
        return redirect('home')
    return render(request, 'signup.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        pw = request.POST['password']
        user = User.objects.filter(email=email, password=pw).first()
        if not user:
            return render(request, 'login.html', {'error': 'Invalid credentials.'})
        request.session['user_id'] = user.id
        return redirect('home')
    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    return redirect('home')


def book_provider(request, provider_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    # Get the service first
    service = get_object_or_404(Service, id=provider_id)

    # Get available providers for this service
    providers = ServiceProvider.objects.filter(service_type=service.service_type)

    if request.method == 'POST':
        user_obj = User.objects.get(id=user_id)
        user_obj.name = request.POST['name']
        user_obj.email = request.POST['email']
        user_obj.phone = request.POST['phone']
        user_obj.address = request.POST['address']
        user_obj.save()

        booking_date = request.POST['booking_date']
        booking_time_raw = request.POST.get('booking_time', '').strip()
        if not booking_time_raw:
            messages.error(request, 'Please select an available time slot.')
            return redirect('book_provider', provider_id=service.id)
        booking_time = datetime.strptime(booking_time_raw, '%H:%M').time()
        preferred_id = request.POST.get('preferred_provider')

        preferred_provider = None
        if preferred_id:
            preferred_provider = ServiceProvider.objects.filter(id=preferred_id).first()

        provider = assign_provider_for_slot(
            service, booking_date, booking_time, preferred_provider
        )

        booking = Booking.objects.create(
            user=user_obj,
            provider=provider,
            service=service,
            booking_date=booking_date,
            booking_time=booking_time,
            status='Provider Assigned' if provider else 'Pending',
        )

        if provider:
            mark_slot_occupied(provider, booking_date, booking_time)

        # Background: emails + notifications (user does not wait)
        send_booking_confirmation_email.delay(booking.id)
        dispatch_notification_task.delay('booking_created', booking_id=booking.id)
        if provider:
            dispatch_notification_task.delay('provider_assigned', booking_id=booking.id)
        schedule_booking_reminders.delay(booking.id)

        return redirect('booking_success')

    # Get selected food from session for cooking services
    selected_food = request.session.get('selected_food', []) if service.service_type == 'cooking' else None

    # Always flatten to a list of names and prices
    if isinstance(selected_food, str):
        selected_food = [item for item in selected_food.split(';') if item]
    elif isinstance(selected_food, list):
        # If it's a list with a single string with semicolons, split that string
        if len(selected_food) == 1 and isinstance(selected_food[0], str) and ';' in selected_food[0]:
            selected_food = [item for item in selected_food[0].split(';') if item]
        # If it's a list of strings, but some strings have semicolons, flatten them
        elif any(';' in s for s in selected_food):
            flat = []
            for s in selected_food:
                flat.extend([item for item in s.split(';') if item])
            selected_food = flat

    from datetime import date as date_cls
    default_date = date_cls.today()
    available_slots = get_available_slots(service, default_date)

    provider_reviews = (
        Review.objects.filter(booking__provider__service_type=service.service_type)
        .select_related('booking__user', 'booking')
        .order_by('-id')[:8]
    )
    user_obj = User.objects.filter(id=user_id).first()

    return render(request, 'book.html', {
        'service': service,
        'providers': providers,
        'selected_food': selected_food,
        'available_slots': available_slots,
        'default_date': default_date.isoformat(),
        'provider_reviews': provider_reviews,
        'user_obj': user_obj,
    })


def booking_success(request):
    return render(request, 'success.html')


def view_bookings(request):
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = Booking.objects.filter(status=status_filter)
    else:
        bookings = Booking.objects.all()

    bookings = bookings.select_related('user', 'provider', 'service')
    return render(request, 'bookings.html', {
        'bookings': bookings,
        'status_filter': status_filter
    })


def my_bookings(request):
    user = get_custom_user_from_request(request)
    if not user:
        return redirect('login')
    request.session['user_id'] = user.id

    # Get bookings for the current user
    bookings = (
        Booking.objects
        .filter(user=user)
        .select_related('provider', 'service', 'dish', 'non_veg_dish')
        .order_by('-id')
    )

    # Get service requests for this user (by user ID or email)
    service_requests = ServiceRequest.objects.filter(
        Q(user=user) | Q(email=user.email)
    ).order_by('-created_at')

    return render(request, 'my_bookings.html', {
        'bookings': bookings,
        'service_requests': service_requests
    })


def leave_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    user_id = request.session.get('user_id')

    if not user_id or booking.user.id != user_id:
        return redirect('login')

    if booking.status != 'Completed':
        messages.error(request, "You can only leave a review for completed bookings.")
        return redirect('my_bookings')

    if request.method == 'POST':
        rating = int(request.POST['rating'])
        comment = request.POST['comment']
        Review.objects.create(
            booking=booking,
            rating=rating,
            comment=comment
        )

        # Update provider's average rating
        provider = booking.provider
        avg_rating = Review.objects.filter(booking__provider=provider).aggregate(Avg('rating'))['rating__avg']
        provider.rating = round(avg_rating or 0, 1)
        provider.save()

        dispatch_notification_task.delay(
            'review_received', booking_id=booking.id, rating=rating,
        )

        return redirect('my_bookings')

    return render(request, 'review.html', {'booking': booking})


def provider_reviews(request, provider_id):
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    reviews = Review.objects.filter(booking__provider=provider).select_related('booking__user')
    return render(request, 'provider_reviews.html', {
        'provider': provider,
        'reviews': reviews
    })


@csrf_exempt
def update_status(request, booking_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        booking = get_object_or_404(Booking, id=booking_id)
        booking.status = new_status
        booking.save()
    return redirect('view_bookings')


def cooking_services(request):
    service_id = request.GET.get('service_id')
    service = None
    if service_id:
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            service = None
    flatbreads = [
        {'name': 'Roti', 'img': 'roti.jpg', 'price': 15},
        {'name': 'Chapati', 'img': 'chapati.jpg', 'price': 15},
        {'name': 'Paratha', 'img': 'paratha.jpg', 'price': 30},
        {'name': 'Naan', 'img': 'naan.png', 'price': 40},
        {'name': 'Phulka', 'img': 'phulka.jpg', 'price': 15},
        {'name': 'Kulcha', 'img': 'kulcha.jpg', 'price': 35},
        {'name': 'Tandoori Roti', 'img': 'tandoori.jpg', 'price': 45},
        {'name': 'Thepla', 'img': 'thepla.jpg', 'price': 25},
    ]
    curries = [
        {'name': 'Paneer Butter Masala', 'img': 'paneer.jpg', 'price': 250},
        {'name': 'Chana Masala', 'img': 'chana.jpg', 'price': 180},
        {'name': 'Aloo Gobi', 'img': 'aloo.jpg', 'price': 160},
        {'name': 'Baingan Bharta', 'img': 'Baingan_Bharta.webp', 'price': 170},
        {'name': 'Dal Tadka', 'img': 'Dal_Tadka.jpg', 'price': 150},
        {'name': 'Malai Kofta', 'img': 'malai.png', 'price': 280},
        {'name': 'Palak Paneer', 'img': 'palak.png', 'price': 260},
        {'name': 'Vegetable Korma', 'img': 'veg.jpg', 'price': 220},
    ]
    rice_items = [
        {'name': 'Biryani', 'img': 'biriyani.png', 'price': 200},
        {'name': 'Pulao (Pilaf)', 'img': 'pulao.png', 'price': 150},
        {'name': 'Jeera Rice', 'img': 'jeera.png', 'price': 120},
        {'name': 'Lemon Rice', 'img': 'lemon.png', 'price': 130},
        {'name': 'Khichdi', 'img': 'khichidi.png', 'price': 140},
        {'name': 'Fried Rice', 'img': 'fried.png', 'price': 160},
        {'name': 'Curd Rice', 'img': 'curd.png', 'price': 120},
        {'name': 'Tamarind Rice', 'img': 'tamarind.png', 'price': 130},
        {'name': 'Steamed Rice', 'img': 'steamed.png', 'price': 100},
        {'name': 'Saffron Rice', 'img': 'safforn.png', 'price': 180},
        {'name': 'Coconut Rice', 'img': 'coconut.png', 'price': 150},
        {'name': 'Vegetable Rice', 'img': 'veg_rice.png', 'price': 160},
    ]
    nv_flatbreads = [
        {'name': 'Roti', 'img': 'roti.jpg', 'price': 15},
        {'name': 'Chapati', 'img': 'chapati.jpg', 'price': 15},
        {'name': 'Paratha', 'img': 'paratha.jpg', 'price': 30},
        {'name': 'Naan', 'img': 'naan.png', 'price': 40},
        {'name': 'Phulka', 'img': 'phulka.jpg', 'price': 15},
        {'name': 'Kulcha', 'img': 'kulcha.jpg', 'price': 35},
        {'name': 'Tandoori Roti', 'img': 'tandoori.jpg', 'price': 45},
        {'name': 'Thepla', 'img': 'thepla.jpg', 'price': 25},
    ]
    nv_curries = [
        {'name': 'Butter Chicken', 'img': 'butter.png', 'price': 350},
        {'name': 'Chicken Curry', 'img': 'chicken.png', 'price': 280},
        {'name': 'Egg Curry', 'img': 'egg_curry.png', 'price': 200},
        {'name': 'Fish Curry', 'img': 'fish_curry.png', 'price': 300},
        {'name': 'Chicken Do Pyaza', 'img': 'chicken_do.png', 'price': 290},
        {'name': 'Chicken Chettinad', 'img': 'chicken_c.jpg', 'price': 320},
        {'name': 'Goan Fish Curry', 'img': 'fish_curry.png', 'price': 310},
        {'name': 'Prawn Masala', 'img': 'prawn.png', 'price': 380},
    ]
    nv_rice_items = [
        {'name': 'Chicken Biryani', 'img': 'chicken_briyani.png', 'price': 280},
        {'name': 'Egg Fried Rice', 'img': 'egg_frie.png', 'price': 180},
        {'name': 'Fish Pulao', 'img': 'fish_pulao.png', 'price': 250},
        {'name': 'Prawn Biryani', 'img': 'prawn_briyani.png', 'price': 350},
        {'name': 'Keema Rice', 'img': 'keema.png', 'price': 220},
        {'name': 'Chicken Pulao', 'img': 'chicken_palvo.png', 'price': 200},
        {'name': 'Mutton Biryani', 'img': 'mutton_briyani.png', 'price': 320},
        {'name': 'Egg Pulao', 'img': 'egg_pulao.png', 'price': 180},
    ]
    selected_food = request.session.get('selected_food', [])
    return render(request, 'core/cooking_services.html', {
        'flatbreads': flatbreads,
        'nv_flatbreads': nv_flatbreads,
        'curries': curries,
        'rice_items': rice_items,
        'nv_rice_items': nv_rice_items,
        'nv_curries': nv_curries,
        'user': request.user,
        'service': service,
        'selected_food': selected_food,
    })


def veg_dishes(request):
    dish_type = request.GET.get('dish_type')
    if dish_type:
        dishes = VegDish.objects.filter(dish_type=dish_type)
    else:
        dishes = VegDish.objects.all()
    return render(request, 'veg_dishes.html', {
        'dishes': dishes,
        'dish_type': dish_type
    })


def non_veg_dishes(request):
    dishes = NonVegDish.objects.all()
    return render(request, 'non_veg_dishes.html', {
        'dishes': dishes
    })


def add_dish(request):
    if request.method == 'POST':
        dish_type = request.POST.get('dish_type')
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')

        if dish_type == 'veg':
            dish_type = request.POST.get('veg_dish_type')
            VegDish.objects.create(
                name=name,
                dish_type=dish_type,
                description=description,
                price=price
            )
        else:
            NonVegDish.objects.create(
                name=name,
                description=description,
                price=price
            )
        return redirect('cooking_services')

    return render(request, 'add_dish.html')


def services(request):
    services = Service.objects.all()
    return render(request, 'core/services.html', {
        'services': services
    })


def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    recommended_services = (
        Service.objects.filter(service_type=service.service_type)
        .exclude(id=service.id)
        .order_by('name')[:4]
    )
    favorite_ids = set()
    user = get_custom_user_from_request(request)
    if user:
        favorite_ids = set(
            Favorite.objects.filter(user=user).values_list('service_id', flat=True)
        )
    return render(request, 'service_detail.html', {
        'service': service,
        'recommended_services': recommended_services,
        'favorite_ids': favorite_ids,
    })


@require_POST
def order_dish(request):
    if not request.session.get('user_id'):
        return JsonResponse({'status': 'error', 'message': 'Please log in to place an order'}, status=401)

    try:
        dish_type = request.POST.get('dish_type')
        dish_id = request.POST.get('dish_id')

        # Get the appropriate dish model
        if dish_type == 'veg':
            dish = get_object_or_404(VegDish, id=dish_id)
        else:
            dish = get_object_or_404(NonVegDish, id=dish_id)

        # Create a booking for the dish
        user = User.objects.get(id=request.session['user_id'])

        # Find a cooking service provider
        provider = ServiceProvider.objects.filter(
            service_type='cooking',
            availability=True
        ).first()

        if not provider:
            return JsonResponse({
                'status': 'error',
                'message': 'No cooking service providers available at the moment'
            }, status=400)

        # Create the booking
        booking = Booking.objects.create(
            user=user,
            provider=provider,
            service=Service.objects.get(service_type='cooking'),
            booking_date=timezone.now().date(),
            booking_time=timezone.now().time(),
            status='Pending'
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Order placed successfully',
            'booking_id': booking.id
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
def order_dish(request, dish_id):
    try:
        dish = VegDish.objects.get(id=dish_id)
        dish_type = 'veg'
    except VegDish.DoesNotExist:
        try:
            dish = NonVegDish.objects.get(id=dish_id)
            dish_type = 'non_veg'
        except NonVegDish.DoesNotExist:
            messages.error(request, 'Dish not found')
            return redirect('cooking_services')

    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        address = request.POST.get('address')
        special_instructions = request.POST.get('special_instructions')

        booking = Booking.objects.create(
            user=request.user,
            dish=dish if dish_type == 'veg' else None,
            non_veg_dish=None if dish_type == 'veg' else dish,
            dish_type=dish_type,
            date=date,
            time=time,
            address=address,
            special_instructions=special_instructions,
            total_amount=dish.price,
            status='Pending'
        )

        return redirect('booking_confirmation', booking_id=booking.id)

    return render(request, 'core/order_form.html', {
        'dish': dish,
        'dish_type': dish_type,
        'today': timezone.now().date()
    })


@login_required
def booking_confirmation(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    return render(request, 'core/booking_confirmation.html', {
        'booking': booking
    })


def book_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    menu_items = MenuItem.objects.all()
    if request.method == 'POST':
        # ... get user details as per your form ...
        selected_items_ids = request.POST.getlist('menu_items')
        selected_items = MenuItem.objects.filter(id__in=selected_items_ids)
        total_price = sum(item.price for item in selected_items)
        # Create booking (add your user/provider logic as needed)
        booking = Booking.objects.create(
            service=service,
            total_price=total_price,
            # ... other fields ...
        )
        booking.menu_items.set(selected_items)
        # ... handle redirect or success ...
        return redirect('success')
    return render(request, 'book.html', {
        'service': service,
        'menu_items': menu_items,
    })


@csrf_exempt
def save_food_selection(request):
    if request.method == 'POST':
        food_items_str = request.POST.get('food_items', '')
        food_items = [item.strip() for item in food_items_str.split('||') if item.strip()]
        service_id = request.POST.get('service_id')

        if not food_items:
            messages.warning(request, 'Please select at least one food item.')
            return redirect('cooking_services')

        if not service_id:
            messages.error(request, 'Service ID missing. Please try again.')
            return redirect('cooking_services')

        request.session['selected_food'] = food_items
        return redirect('book_provider', provider_id=service_id)
    return redirect('cooking_services')


@csrf_exempt
def submit_service_request(request):
    if request.method == 'POST':
        # Get form data
        service_type = request.POST.get('service_type')
        service_name = request.POST.get('service_name')
        description = request.POST.get('description')
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        date = request.POST.get('date')
        time = request.POST.get('time')

        # Print debug information
        print(f"Submitting service request: {service_type}, {service_name}, {email}")

        # Associate with user if logged in
        user = get_custom_user_from_request(request)
        if user:
            request.session['user_id'] = user.id
            print(f"Found user: {user.name}, {user.email}")
            # Use user information if not provided
            if not name:
                name = user.name
            if not email:
                email = user.email
            if not phone:
                phone = user.phone
            if not address:
                address = user.address
        else:
            print("No custom user found in session or authenticated request")

        # Set default price based on service type
        price = None
        if service_type == 'cleaning':
            price = 1500.00
        elif service_type == 'maintenance':
            price = 2000.00
        elif service_type == 'garden':
            price = 1200.00
        elif service_type == 'home_appliance':
            price = 1800.00
        elif service_type == 'security':
            price = 2500.00
        elif service_type == 'food':
            price = 1000.00

        # Create service request
        service_request = ServiceRequest.objects.create(
            service_type=service_type,
            service_name=service_name,
            description=description,
            user=user,  # Associate with user
            name=name,
            email=email,
            phone=phone,
            address=address,
            date=date,
            time=time,
            price=price,  # Add price
            status='not_done'
        )

        print(f"Created service request with ID: {service_request.id}")

        messages.success(request, 'Your service request has been submitted successfully!')
        # Redirect to my_bookings instead of home
        return redirect('my_bookings')

    return redirect('home')


@csrf_exempt
@require_POST
def process_payment(request):
    """Handle payment processing from the frontend"""
    try:
        # Get data from request
        booking_id = request.POST.get('booking_id')
        amount = request.POST.get('amount')
        payment_mode = request.POST.get('payment_mode')

        booking = get_object_or_404(Booking, id=booking_id)

        if booking.payments.filter(status='completed').exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Payment already completed for this booking.',
            }, status=400)

        # Get client IP and user agent
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Create payment record
        payment_data = {
            'booking': booking,
            'amount': amount,
            'mode': payment_mode,
            'status': 'pending',
            'ip_address': ip_address,
            'user_agent': user_agent,
        }

        # Add specific details based on payment mode
        if payment_mode in ['googlepay', 'phonepe', 'paytm']:
            # For UPI payments, we'll simulate transaction ID
            import uuid
            payment_data['transaction_id'] = f"{payment_mode.upper()}{uuid.uuid4().hex[:8]}"
            payment_data['upi_id'] = request.POST.get('upi_id', '')

        elif payment_mode in ['debitcard', 'creditcard']:
            # For card payments, store last 4 digits (simulated)
            card_number = request.POST.get('card_number', '')
            if card_number:
                payment_data['card_last_four'] = card_number[-4:] if len(card_number) >= 4 else '0000'
                payment_data['card_type'] = request.POST.get('card_type', 'Unknown')
            payment_data['transaction_id'] = f"CARD{uuid.uuid4().hex[:8]}"

        elif payment_mode == 'cod':
            # Cash on Delivery
            payment_data['status'] = 'pending'
            payment_data['transaction_id'] = f"COD{booking_id}{timezone.now().strftime('%Y%m%d%H%M')}"

        elif payment_mode == 'paylater':
            # Pay Later - set due date to 30 days from now
            payment_data['due_date'] = timezone.now() + timedelta(days=30)
            payment_data['repayment_terms'] = "Payment due within 30 days. No interest for first 15 days. 2% monthly interest after 15 days."
            payment_data['transaction_id'] = f"LATER{booking_id}{timezone.now().strftime('%Y%m%d%H%M')}"

        # Create the payment
        payment = Payment.objects.create(**payment_data)

        # For certain payment modes, mark as completed immediately
        if payment_mode in ['googlepay', 'phonepe', 'paytm', 'debitcard', 'creditcard']:
            payment.status = 'completed'
            payment.paid_at = timezone.now()
            payment.save()
        elif payment_mode in ['cod', 'paylater']:
            # These remain pending until actual payment
            payment.status = 'pending'
            payment.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Payment processed successfully',
            'payment_id': payment.id,
            'transaction_id': payment.transaction_id
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@staff_member_required
def analytics_dashboard(request):
    """Admin-only analytics dashboard with real-time business insights."""
    now = timezone.now()
    today = now.date()

    # KPI cards
    total_bookings = Booking.objects.count()
    completed_services = Booking.objects.filter(status='Completed').count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    active_providers = ServiceProvider.objects.filter(availability=True).count()
    registered_users = User.objects.count()

    # Most popular services (top 5) — full Service objects for images + charts
    popular_services = list(
        Service.objects.annotate(booking_count=Count('booking'))
        .order_by('-booking_count')[:5]
    )

    # Top performing providers by rating and completed bookings
    top_providers = (
        ServiceProvider.objects.annotate(
            completed_bookings=Count(
                'booking',
                filter=Q(booking__status='Completed'),
            )
        )
        .order_by('-rating', '-completed_bookings')[:5]
    )

    # Peak booking hours (merge booking_time and cooking time fields)
    hour_counts = defaultdict(int)
    for row in (
        Booking.objects.exclude(booking_time__isnull=True)
        .annotate(hour=ExtractHour('booking_time'))
        .values('hour')
        .annotate(count=Count('id'))
    ):
        hour_counts[row['hour']] += row['count']
    for row in (
        Booking.objects.filter(booking_time__isnull=True)
        .exclude(time__isnull=True)
        .annotate(hour=ExtractHour('time'))
        .values('hour')
        .annotate(count=Count('id'))
    ):
        hour_counts[row['hour']] += row['count']
    peak_hours = sorted(hour_counts.items(), key=lambda x: -x[1])[:5]
    max_peak_count = peak_hours[0][1] if peak_hours else 1
    peak_hours_display = [
        {
            'hour': h,
            'label': datetime.strptime(str(h), '%H').strftime('%I %p'),
            'count': c,
        }
        for h, c in peak_hours
    ]

    # Recent bookings (latest 10)
    recent_bookings = (
        Booking.objects.select_related('user', 'service', 'provider', 'dish', 'non_veg_dish')
        .order_by('-id')[:10]
    )

    # Revenue insights
    completed_payments = Payment.objects.filter(status='completed')
    daily_revenue = completed_payments.filter(
        Q(paid_at__date=today) | Q(paid_at__isnull=True, created_at__date=today)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    monthly_revenue = completed_payments.filter(
        Q(paid_at__year=now.year, paid_at__month=now.month)
        | Q(paid_at__isnull=True, created_at__year=now.year, created_at__month=now.month)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Monthly revenue trend for line chart
    monthly_revenue_trend = list(
        completed_payments.exclude(paid_at__isnull=True)
        .annotate(month=TruncMonth('paid_at'))
        .values('month')
        .annotate(revenue=Sum('amount'))
        .order_by('month')
    )
    if not monthly_revenue_trend:
        monthly_revenue_trend = list(
            completed_payments.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(revenue=Sum('amount'))
            .order_by('month')
        )

    # Booking status distribution
    status_distribution = {
        'Pending': Booking.objects.filter(status='Pending').count(),
        'Provider Assigned': Booking.objects.filter(status='Provider Assigned').count(),
        'Accepted': Booking.objects.filter(status='Accepted').count(),
        'In Progress': Booking.objects.filter(status='In Progress').count(),
        'Completed': Booking.objects.filter(status='Completed').count(),
        'Cancelled': Booking.objects.filter(status='Cancelled').count(),
    }

    # Chart.js data payloads
    chart_popular_labels = [s.name for s in popular_services]
    chart_popular_data = [s.booking_count for s in popular_services]

    chart_status_labels = list(status_distribution.keys())
    chart_status_data = list(status_distribution.values())

    chart_revenue_labels = [
        row['month'].strftime('%b %Y') if row['month'] else 'N/A'
        for row in monthly_revenue_trend
    ]
    chart_revenue_data = [
        float(row['revenue'] or 0) for row in monthly_revenue_trend
    ]

    context = {
        'total_bookings': total_bookings,
        'completed_services': completed_services,
        'total_revenue': total_revenue,
        'active_providers': active_providers,
        'registered_users': registered_users,
        'popular_services': popular_services,
        'top_providers': top_providers,
        'peak_hours_display': peak_hours_display,
        'max_peak_count': max_peak_count,
        'recent_bookings': recent_bookings,
        'daily_revenue': daily_revenue,
        'monthly_revenue': monthly_revenue,
        'status_distribution': status_distribution,
        'chart_popular_labels': json.dumps(chart_popular_labels),
        'chart_popular_data': json.dumps(chart_popular_data),
        'chart_status_labels': json.dumps(chart_status_labels),
        'chart_status_data': json.dumps(chart_status_data),
        'chart_revenue_labels': json.dumps(chart_revenue_labels),
        'chart_revenue_data': json.dumps(chart_revenue_data),
    }
    return render(request, 'analytics.html', context)


# ─── Marketplace Features ───────────────────────────────────────────────────

def search_services(request):
    """Search and filter services."""
    q = request.GET.get('q', '').strip()
    service_type = request.GET.get('service_type', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    min_rating = request.GET.get('min_rating', '')
    location = request.GET.get('location', '').strip()
    sort = request.GET.get('sort', '')

    services = Service.objects.all()

    if q:
        services = services.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(service_type__icontains=q)
        )
    if service_type:
        services = services.filter(service_type=service_type)
    if min_price:
        services = services.filter(base_price__gte=min_price)
    if max_price:
        services = services.filter(base_price__lte=max_price)
    if location:
        matching_types = ServiceProvider.objects.filter(
            location__icontains=location
        ).values_list('service_type', flat=True).distinct()
        services = services.filter(service_type__in=matching_types)

    services = services.annotate(
        booking_count=Count('booking'),
        avg_rating=Avg('booking__provider__rating'),
    )
    if min_rating:
        services = services.filter(avg_rating__gte=float(min_rating))

    if sort == 'price_low':
        services = services.order_by('base_price')
    elif sort == 'price_high':
        services = services.order_by('-base_price')
    elif sort == 'rating':
        services = services.order_by('-avg_rating')
    elif sort == 'popular':
        services = services.order_by('-booking_count')
    else:
        services = services.order_by('name')

    favorite_ids = set()
    user = get_custom_user_from_request(request)
    if user:
        favorite_ids = set(Favorite.objects.filter(user=user).values_list('service_id', flat=True))

    return render(request, 'search.html', {
        'services': services,
        'service_types': SERVICE_TYPE_CHOICES,
        'favorite_ids': favorite_ids,
        'q': q,
        'filters': request.GET,
    })


def favorites_list(request):
    user = get_custom_user_from_request(request)
    if not user:
        return redirect('login')
    favorites = Favorite.objects.filter(user=user).select_related('service')
    return render(request, 'favorites.html', {'favorites': favorites})


@require_POST
def toggle_favorite(request, service_id):
    user = get_custom_user_from_request(request)
    if not user:
        return redirect('login')
    service = get_object_or_404(Service, id=service_id)
    fav, created = Favorite.objects.get_or_create(user=user, service=service)
    if not created:
        fav.delete()
        messages.info(request, f'Removed {service.name} from favorites.')
    else:
        messages.success(request, f'Saved {service.name} to favorites!')
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url or 'home')


def notifications_list(request):
    user = get_custom_user_from_request(request)
    if not user:
        return redirect('login')
    notifications = Notification.objects.filter(user=user).select_related('booking')
    return render(request, 'notifications.html', {'notifications': notifications})


@require_POST
def mark_notification_read(request, notification_id):
    user = get_custom_user_from_request(request)
    if not user:
        return redirect('login')
    Notification.objects.filter(id=notification_id, user=user).update(is_read=True)
    return redirect('notifications_list')


@require_POST
def mark_all_notifications_read(request):
    user = get_custom_user_from_request(request)
    if not user:
        return redirect('login')
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    return redirect('notifications_list')


def notifications_api(request):
    """JSON API for notification dropdown and real-time polling fallback."""
    user = get_custom_user_from_request(request)
    from .provider_utils import get_provider_from_request
    provider = get_provider_from_request(request)

    if not user and not provider:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    qs = Notification.objects.all()
    if user:
        qs = qs.filter(user=user)
    else:
        qs = qs.filter(provider=provider)

    unread_count = qs.filter(is_read=False).count()
    recent = qs.order_by('-created_at')[:15]
    notifications = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'notification_type': n.notification_type,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%b %d, %Y %H:%M'),
        'booking_id': n.booking_id,
    } for n in recent]

    return JsonResponse({
        'unread_count': unread_count,
        'notifications': notifications,
    })


def available_slots_api(request, service_id):
    """JSON API: available time slots for a service on a given date."""
    service = get_object_or_404(Service, id=service_id)
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'slots': []})
    from datetime import datetime
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'slots': []})
    slots = get_available_slots(service, booking_date)
    return JsonResponse({'slots': slots})


def get_recommendations(user):
    last_booking = Booking.objects.filter(
        user=user
    ).order_by('-id').first()

    if not last_booking:
        return Service.objects.all()[:4]

    service_type = last_booking.service.service_type

    recommendations = Service.objects.filter(
        service_type=service_type
    ).exclude(
        id=last_booking.service.id
    )[:4]

    return recommendations