from django.urls import path
from . import views
from . import provider_views
from . import chat_views
from . import payment_views
from .views import create_admin

urlpatterns = [
    path('create-admin/', views.create_admin),
    path('', views.home, name='home'),
    path('book/<int:provider_id>/', views.book_provider, name='book_provider'),
    path('success/', views.booking_success, name='booking_success'),
    path('bookings/', views.view_bookings, name='view_bookings'),
    # ↓ new ones:
    path('signup/', views.signup, name='signup'),
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('review/<int:booking_id>/', views.leave_review, name='leave_review'),
    # Merge these two paths
    path('provider-reviews/<int:provider_id>/', views.provider_reviews, name='provider_reviews'),
    # Cooking service URLs
    path('cooking-services/', views.cooking_services, name='cooking_services'),
    path('veg-dishes/', views.veg_dishes, name='veg_dishes'),
    path('non-veg-dishes/', views.non_veg_dishes, name='non_veg_dishes'),
    path('add-dish/', views.add_dish, name='add_dish'),
    path('order-dish/', views.order_dish, name='order_dish'),
    path('order-dish/<int:dish_id>/', views.order_dish, name='order_dish'),
    path('booking-confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    # Service URLs
    path('services/', views.services, name='services'),
    path('services/<int:service_id>/', views.service_detail, name='service_detail'),
    path('save-food-selection/', views.save_food_selection, name='save_food_selection'),
    path('submit-service-request/', views.submit_service_request, name='submit_service_request'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('payment/<int:booking_id>/', payment_views.payment_checkout, name='payment_checkout'),
    path('payment/<int:booking_id>/create-order/', payment_views.create_razorpay_order_api, name='create_razorpay_order'),
    path('payment/verify/', payment_views.verify_razorpay_payment_api, name='verify_razorpay_payment'),
    path('payment/history/', payment_views.payment_history, name='payment_history'),
    path('payment/invoice/<int:invoice_id>/', payment_views.view_invoice, name='view_invoice'),
    path('payment/invoice/<int:invoice_id>/download/', payment_views.download_invoice, name='download_invoice'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    # Provider Management System
    path('provider/login/', provider_views.provider_login, name='provider_login'),
    path('provider/logout/', provider_views.provider_logout, name='provider_logout'),
    path('provider/dashboard/', provider_views.provider_dashboard, name='provider_dashboard'),
    path('provider/profile/', provider_views.provider_profile, name='provider_profile'),
    path('provider/accept/<int:booking_id>/', provider_views.accept_booking, name='accept_booking'),
    path('provider/reject/<int:booking_id>/', provider_views.reject_booking, name='reject_booking'),
    path('provider/start/<int:booking_id>/', provider_views.start_service, name='start_service'),
    path('provider/complete/<int:booking_id>/', provider_views.complete_service, name='complete_service'),
    path('provider/notifications/', provider_views.provider_notifications, name='provider_notifications'),
    path('provider/notifications/<int:notification_id>/read/', provider_views.provider_mark_notification_read, name='provider_mark_notification_read'),
    # Marketplace
    path('search/', views.search_services, name='search_services'),
    path('favorites/', views.favorites_list, name='favorites_list'),
    path('favorites/toggle/<int:service_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/slots/<int:service_id>/', views.available_slots_api, name='available_slots_api'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    # Real-time chat (available after booking accepted)
    path('chat/<int:booking_id>/', chat_views.booking_chat, name='booking_chat'),
    path('chat/<int:booking_id>/read/', chat_views.mark_chat_read, name='mark_chat_read'),
    path('provider/chat/<int:booking_id>/', chat_views.provider_booking_chat, name='provider_booking_chat'),
    path('api/chat/<int:booking_id>/messages/', chat_views.chat_messages_api, name='chat_messages_api'),
    path('api/chat/<int:booking_id>/send/', chat_views.chat_send_api, name='chat_send_api'),
]
