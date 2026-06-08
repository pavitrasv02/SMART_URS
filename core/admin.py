from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.contrib import messages
from django import forms
from .models import (
    User, ServiceProvider, Service, Booking, Payment, Review,
    CookingService, VegDish, NonVegDish, MenuItem, Bread, ServiceRequest,
    Notification, Favorite, ProviderTimeSlot, ChatRoom, ChatMessage, Invoice,
)
from django.contrib import admin
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

admin.site.register(User)
admin.site.register(Review)
admin.site.register(Bread)


def _latest_payment(booking):
    """Most recent payment for a booking (by id, then created_at)."""
    return booking.payments.order_by('-id').first()


class BookingAdminForm(forms.ModelForm):
    payment_status = forms.ChoiceField(
        choices=Payment.PAYMENT_STATUS_CHOICES,
        required=False,
        label='Payment Status',
        help_text='Change the status of the latest payment for this booking'
    )

    class Meta:
        model = Booking
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial value for payment_status if booking has payments
        if self.instance and self.instance.pk and self.instance.payments.exists():
            latest_payment = _latest_payment(self.instance)
            if latest_payment:
                self.fields['payment_status'].initial = latest_payment.status
        else:
            # Hide payment_status field if no payments exist
            del self.fields['payment_status']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'booking_link',
        'user_name',
        'service_name_display',
        'amount_display',
        'mode_display',
        'status_display',
        'transaction_id',
        'created_at_display',
        'paid_at_display'
    )

    list_filter = (
        'status',
        'mode',
        'created_at',
        'paid_at',
        'booking__service__service_type'
    )

    search_fields = (
        'booking__user__name',
        'booking__user__email',
        'transaction_id',
        'booking__service__name',
        'upi_id'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'booking_details',
        'payment_summary'
    )

    ordering = ('-created_at',)
    list_per_page = 50

    fieldsets = (
        ('Payment Information', {
            'fields': ('booking', 'amount', 'mode', 'status', 'transaction_id')
        }),
        ('Payment Details', {
            'fields': ('card_last_four', 'card_type', 'upi_id'),
            'classes': ('collapse',)
        }),
        ('Pay Later Details', {
            'fields': ('due_date', 'repayment_terms'),
            'classes': ('collapse',)
        }),
        ('Technical Details', {
            'fields': ('payment_gateway_response', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('booking_details', 'payment_summary'),
            'classes': ('wide',)
        })
    )

    def booking_link(self, obj):
        if obj.booking:
            url = reverse('admin:core_booking_change', args=[obj.booking.id])
            return format_html('<a href="{}">{}</a>', url, f"Booking #{obj.booking.id}")
        return "-"
    booking_link.short_description = "Booking"
    booking_link.admin_order_field = 'booking'

    def user_name(self, obj):
        return obj.user.name if obj.user else "-"
    user_name.short_description = "Customer"
    user_name.admin_order_field = 'booking__user__name'

    def service_name_display(self, obj):
        return obj.service_name
    service_name_display.short_description = "Service"

    def amount_display(self, obj):
        return format_html('<strong>₹{}</strong>', obj.amount)
    amount_display.short_description = "Amount"
    amount_display.admin_order_field = 'amount'

    def mode_display(self, obj):
        colors = {
            'googlepay': '#4285f4',
            'phonepe': '#5f259f',
            'paytm': '#00baf2',
            'debitcard': '#ff6b35',
            'creditcard': '#ffa500',
            'cod': '#28a745',
            'paylater': '#dc3545',
            'netbanking': '#17a2b8',
            'wallet': '#6f42c1',
            'emi': '#fd7e14'
        }
        color = colors.get(obj.mode, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_mode_display()
        )
    mode_display.short_description = "Payment Mode"
    mode_display.admin_order_field = 'mode'

    def status_display(self, obj):
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d',
            'refunded': '#fd7e14'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display().upper()
        )
    status_display.short_description = "Status"
    status_display.admin_order_field = 'status'

    def created_at_display(self, obj):
        return obj.created_at.strftime('%d %b %Y, %I:%M %p') if obj.created_at else "-"
    created_at_display.short_description = "Created"
    created_at_display.admin_order_field = 'created_at'

    def paid_at_display(self, obj):
        return obj.paid_at.strftime('%d %b %Y, %I:%M %p') if obj.paid_at else "-"
    paid_at_display.short_description = "Paid At"
    paid_at_display.admin_order_field = 'paid_at'

    def booking_details(self, obj):
        if not obj.booking:
            return "-"

        booking = obj.booking
        details = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <h4 style="margin-top: 0; color: #495057;">Booking Details</h4>
            <p><strong>Booking ID:</strong> #{booking.id}</p>
            <p><strong>Customer:</strong> {booking.user.name} ({booking.user.email})</p>
            <p><strong>Phone:</strong> {booking.user.phone}</p>
            <p><strong>Service:</strong> {obj.service_name}</p>
            <p><strong>Provider:</strong> {booking.provider.name if booking.provider else 'Not Assigned'}</p>
            <p><strong>Booking Date:</strong> {booking.booking_date}</p>
            <p><strong>Booking Time:</strong> {booking.booking_time}</p>
            <p><strong>Status:</strong> {booking.get_status_display()}</p>
            <p><strong>Address:</strong> {booking.address}</p>
        </div>
        """
        return mark_safe(details)
    booking_details.short_description = "Booking Information"

    def payment_summary(self, obj):
        summary = f"""
        <div style="background: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <h4 style="margin-top: 0; color: #495057;">Payment Summary</h4>
            <p><strong>Amount:</strong> ₹{obj.amount}</p>
            <p><strong>Payment Mode:</strong> {obj.get_mode_display()}</p>
            <p><strong>Status:</strong> {obj.get_status_display()}</p>
            <p><strong>Transaction ID:</strong> {obj.transaction_id or 'Not Available'}</p>
        """

        if obj.mode in ['debitcard', 'creditcard'] and obj.card_last_four:
            summary += f"<p><strong>Card:</strong> **** **** **** {obj.card_last_four} ({obj.card_type or 'Unknown'})</p>"

        if obj.mode in ['googlepay', 'phonepe', 'paytm'] and obj.upi_id:
            summary += f"<p><strong>UPI ID:</strong> {obj.upi_id}</p>"

        if obj.mode == 'paylater' and obj.due_date:
            summary += f"<p><strong>Due Date:</strong> {obj.due_date.strftime('%d %b %Y')}</p>"
            if obj.repayment_terms:
                summary += f"<p><strong>Terms:</strong> {obj.repayment_terms}</p>"

        if obj.created_at:
            summary += f"<p><strong>Created:</strong> {obj.created_at.strftime('%d %b %Y, %I:%M %p')}</p>"

        if obj.paid_at:
            summary += f"<p><strong>Paid:</strong> {obj.paid_at.strftime('%d %b %Y, %I:%M %p')}</p>"

        summary += "</div>"
        return mark_safe(summary)
    payment_summary.short_description = "Payment Details"

    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_refunded']

    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', paid_at=timezone.now())
        self.message_user(request, f'{updated} payments marked as completed.')
    mark_as_completed.short_description = "Mark selected payments as completed"

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_as_failed.short_description = "Mark selected payments as failed"

    def mark_as_refunded(self, request, queryset):
        updated = queryset.update(status='refunded')
        self.message_user(request, f'{updated} payments marked as refunded.')
    mark_as_refunded.short_description = "Mark selected payments as refunded"

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            new_status = form.cleaned_data.get('status')
            if new_status == 'completed' and not obj.paid_at:
                obj.paid_at = timezone.now()
            elif new_status != 'completed':
                obj.paid_at = None

        super().save_model(request, obj, form, change)

        if change and obj.status == 'completed' and obj.booking_id:
            try:
                from .payment_utils import create_invoice_for_booking
                create_invoice_for_booking(obj.booking)
            except Exception:
                pass


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
    list_display = ('id', 'user', 'provider', 'service', 'status', 'payment_status_display', 'booking_date', 'booking_time')
    list_filter = ('status', 'booking_date', 'payments__status')
    search_fields = ('user__name', 'provider__name', 'service__name')

    def save_model(self, request, obj, form, change):
        if change:
            old = Booking.objects.get(pk=obj.pk)
            if (
                old.status != "Provider Assigned"
                and obj.status == "Provider Assigned"
            ):
                from core.tasks import send_provider_assigned_email_task, dispatch_notification_task
                send_provider_assigned_email_task.delay(obj.id)
                dispatch_notification_task.delay('provider_assigned', booking_id=obj.id)

        super().save_model(request, obj, form, change)

        # Custom payment_status field is not on Booking — persist to latest Payment row
        if change and 'payment_status' in form.cleaned_data and obj.payments.exists():
            new_status = form.cleaned_data['payment_status']
            latest_payment = _latest_payment(obj)
            if latest_payment and latest_payment.status != new_status:
                latest_payment.status = new_status
                if new_status == 'completed' and not latest_payment.paid_at:
                    latest_payment.paid_at = timezone.now()
                elif new_status != 'completed':
                    latest_payment.paid_at = None
                latest_payment.save(update_fields=['status', 'paid_at', 'updated_at'])

                if new_status == 'completed':
                    try:
                        from .payment_utils import create_invoice_for_booking
                        create_invoice_for_booking(obj)
                    except Exception:
                        pass

                messages.success(
                    request,
                    f'Payment status updated to {latest_payment.get_status_display()}',
                )

    def payment_status_display(self, obj):
        latest_payment = _latest_payment(obj)
        if not latest_payment:
            return format_html('<span style="color: #dc3545;">No Payment</span>')

        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d',
            'refunded': '#fd7e14'
        }
        color = colors.get(latest_payment.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            latest_payment.get_status_display().upper()
        )
    payment_status_display.short_description = "Payment Status"
    payment_status_display.admin_order_field = 'payments__status'

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ('Basic Information', {
                'fields': ('user', 'provider', 'service', 'status')
            }),
            ('Booking Details', {
                'fields': ('booking_date', 'booking_time', 'date', 'time', 'address')
            }),
            ('Financial Details', {
                'fields': ('total_price', 'total_amount')
            }),
        ]

        # Add payment status field if payments exist
        if obj and obj.payments.exists():
            fieldsets.append(
                ('Payment Management', {
                    'fields': ('payment_status',),
                    'description': 'Manage payment status for this booking'
                })
            )

        # Add service-specific fields based on service type
        if obj and obj.service and obj.service.service_type:
            service_type = obj.service.service_type
            service_fields = {
                'cleaning': {
                    'fields': ('special_instructions',),
                    'description': 'Cleaning service specific details'
                },
                'maintenance': {
                    'fields': ('special_instructions',),
                    'description': 'Maintenance service specific details'
                },
                'gardening': {
                    'fields': ('special_instructions',),
                    'description': 'Gardening service specific details'
                },
                'automation': {
                    'fields': ('special_instructions',),
                    'description': 'Home automation service specific details'
                },
                'security': {
                    'fields': ('special_instructions',),
                    'description': 'Security service specific details'
                },
            }

            if service_type in service_fields:
                fieldsets.append(
                    ('Service-Specific Details', {
                        'fields': service_fields[service_type]['fields'],
                        'description': service_fields[service_type]['description'],
                        'classes': ('collapse',)
                    })
                )

        # Add food service-specific fields based on dish type
        if obj and obj.dish_type:
            if obj.dish_type == 'veg':
                fieldsets.append(
                    ('Food Service Details', {
                        'fields': ('dish_type', 'dish', 'special_instructions'),
                        'description': 'Vegetarian food service details'
                    })
                )
            elif obj.dish_type == 'non_veg':
                fieldsets.append(
                    ('Food Service Details', {
                        'fields': ('dish_type', 'non_veg_dish', 'special_instructions'),
                        'description': 'Non-vegetarian food service details'
                    })
                )

        # Add payment information if payments exist
        if obj and obj.payments.exists():
            fieldsets.append(
                ('Payment Information', {
                    'fields': ('payment_summary',),
                    'classes': ('wide',)
                })
            )

        return tuple(fieldsets)

    readonly_fields = ('payment_summary',)

    def payment_summary(self, obj):
        if not obj or not obj.payments.exists():
            return "No payments found"

        payments = obj.payments.all().order_by('-created_at')
        summary = '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">'
        summary += '<h4 style="margin-top: 0; color: #495057;">Payment History</h4>'

        for payment in payments:
            status_colors = {
                'pending': '#ffc107',
                'processing': '#17a2b8',
                'completed': '#28a745',
                'failed': '#dc3545',
                'cancelled': '#6c757d',
                'refunded': '#fd7e14'
            }
            color = status_colors.get(payment.status, '#6c757d')

            summary += f'''
            <div style="border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background: white;">
                <p><strong>Amount:</strong> ₹{payment.amount}</p>
                <p><strong>Mode:</strong> {payment.get_mode_display()}</p>
                <p><strong>Status:</strong> <span style="color: {color}; font-weight: bold;">{payment.get_status_display().upper()}</span></p>
                <p><strong>Transaction ID:</strong> {payment.transaction_id or 'N/A'}</p>
                <p><strong>Created:</strong> {payment.created_at.strftime('%d %b %Y, %I:%M %p') if payment.created_at else 'N/A'}</p>
                {f'<p><strong>Paid At:</strong> {payment.paid_at.strftime("%d %b %Y, %I:%M %p")}</p>' if payment.paid_at else ''}
            </div>
            '''

        summary += '</div>'
        return mark_safe(summary)
    payment_summary.short_description = "Payment Details"

    actions = ['mark_payment_completed', 'mark_payment_failed']

    def mark_payment_completed(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for booking in queryset:
            pending_payments = booking.payments.filter(status='pending')
            updated += pending_payments.update(status='completed', paid_at=timezone.now())
        self.message_user(request, f'{updated} payments marked as completed.')
    mark_payment_completed.short_description = "Mark pending payments as completed"

    def mark_payment_failed(self, request, queryset):
        updated = 0
        for booking in queryset:
            pending_payments = booking.payments.filter(status='pending')
            updated += pending_payments.update(status='failed')
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_payment_failed.short_description = "Mark pending payments as failed"


@admin.register(CookingService)
class CookingServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'cuisine_type', 'meal_type', 'price', 'is_available', 'chef_speciality')
    list_filter = ('category', 'cuisine_type', 'meal_type', 'is_available', 'chef_speciality')
    search_fields = ('name', 'description', 'ingredients', 'dietary_info')

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Basic Information', {
                'fields': ('name', 'category', 'description', 'price', 'is_available')
            }),
            ('Service-Specific Details', {
                'fields': ('cooking_option', 'cuisine_type', 'meal_type', 'preparation_time', 'serving_size', 'chef_speciality'),
                'description': 'Select the specific service option based on the service type',
                'classes': ('collapse',)
            }),
            ('Dietary Information', {
                'fields': ('ingredients', 'dietary_info'),
                'description': 'Ingredients and dietary information',
                'classes': ('collapse',)
            }),
        )
        return fieldsets

@admin.register(VegDish)
class VegDishAdmin(admin.ModelAdmin):
    list_display = ('name', 'dish_type', 'price', 'is_available')
    list_filter = ('dish_type', 'is_available')
    search_fields = ('name', 'description')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'dish_type', 'price', 'is_available')
        }),
        ('Details', {
            'fields': ('description',),
            'description': 'Vegetarian dish details',
            'classes': ('collapse',)
        }),
    )

@admin.register(NonVegDish)
class NonVegDishAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name', 'description')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'price', 'is_available')
        }),
        ('Details', {
            'fields': ('description',),
            'description': 'Non-vegetarian dish details',
            'classes': ('collapse',)
        }),
    )

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'cooking_type')
    list_filter = ('cooking_type',)
    search_fields = ('name',)
    ordering = ('cooking_type', 'name')
    list_per_page = 50

@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'service_type', 'location', 'rating', 'availability',
        'total_jobs', 'completed_jobs', 'total_earnings_display',
    )
    list_filter = ('service_type', 'availability')
    search_fields = ('name', 'email', 'phone', 'location', 'description')
    readonly_fields = ('performance_summary',)
    actions = ['deactivate_providers', 'activate_providers']

    def total_jobs(self, obj):
        return Booking.objects.filter(provider=obj).count()
    total_jobs.short_description = 'Total Jobs'

    def completed_jobs(self, obj):
        return Booking.objects.filter(provider=obj, status='Completed').count()
    completed_jobs.short_description = 'Completed'

    def total_earnings_display(self, obj):
        from django.db.models import Sum
        from .models import Payment
        total = Payment.objects.filter(
            booking__provider=obj, booking__status='Completed', status='completed'
        ).aggregate(t=Sum('amount'))['t'] or 0
        return format_html('<strong>₹{}</strong>', total)
    total_earnings_display.short_description = 'Earnings'

    def performance_summary(self, obj):
        if not obj:
            return '-'
        total = Booking.objects.filter(provider=obj).count()
        completed = Booking.objects.filter(provider=obj, status='Completed').count()
        pending = Booking.objects.filter(provider=obj, status='Provider Assigned').count()
        return format_html(
            '<div style="padding:12px;background:#f8f9fa;border-radius:8px;">'
            '<p><strong>Total Bookings:</strong> {}</p>'
            '<p><strong>Completed:</strong> {}</p>'
            '<p><strong>Awaiting Action:</strong> {}</p>'
            '<p><strong>Rating:</strong> {}</p>'
            '<p><strong>Active:</strong> {}</p></div>',
            total, completed, pending, obj.rating,
            'Yes' if obj.availability else 'No (Deactivated)',
        )
    performance_summary.short_description = 'Performance'

    def deactivate_providers(self, request, queryset):
        queryset.update(availability=False)
        self.message_user(request, f'{queryset.count()} provider(s) deactivated.')
    deactivate_providers.short_description = 'Deactivate selected providers'

    def activate_providers(self, request, queryset):
        queryset.update(availability=True)
        self.message_user(request, f'{queryset.count()} provider(s) activated.')
    activate_providers.short_description = 'Activate selected providers'

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Basic Information', {
                'fields': ('name', 'email', 'phone', 'password', 'service_type', 'location', 'rating')
            }),
            ('Service Details', {
                'fields': ('description', 'experience_years', 'hourly_rate', 'availability')
            }),
            ('Performance', {
                'fields': ('performance_summary',),
            }),
            ('Additional Information', {
                'fields': ('certifications', 'languages', 'working_hours', 'service_areas')
            }),
        )

        # Add service-specific fields based on service type
        if obj and obj.service_type:
            service_fields = {
                'cleaning': ('cleaning_option',),
                'maintenance': ('maintenance_option',),
                'gardening': ('gardening_option',),
                'automation': ('automation_option',),
                'security': ('security_option',),
            }
            if obj.service_type in service_fields:
                fieldsets += (
                    ('Service-Specific Details', {
                        'fields': service_fields[obj.service_type],
                        'description': 'Select the specific service option based on the service type'
                    }),
                )

        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.service_type:
            # Hide all service-specific fields except the one matching the service type
            service_fields = {
                'cleaning': ['maintenance_option', 'gardening_option', 'automation_option', 'security_option'],
                'maintenance': ['cleaning_option', 'gardening_option', 'automation_option', 'security_option'],
                'gardening': ['cleaning_option', 'maintenance_option', 'automation_option', 'security_option'],
                'automation': ['cleaning_option', 'maintenance_option', 'gardening_option', 'security_option'],
                'security': ['cleaning_option', 'maintenance_option', 'gardening_option', 'automation_option'],
            }
            if obj.service_type in service_fields:
                for field in service_fields[obj.service_type]:
                    if field in form.base_fields:
                        form.base_fields[field].widget = form.base_fields[field].hidden_widget()
        return form

    class Media:
        js = ('admin/js/service_admin.js',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'base_price', 'image_name', 'duration_hours')
    list_editable = ('image_name',)
    list_filter = ('service_type',)
    search_fields = ('name', 'description', 'includes', 'image_name')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'image_name':
            kwargs['help_text'] = 'Enter image filename from static/images/services/'
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Basic Information', {
                'fields': ('name', 'service_type', 'description', 'base_price', 'image_name')
            }),
            ('Additional Information', {
                'fields': ('duration_hours', 'location_type', 'square_footage', 'floor_count', 'includes', 'price_per_hour', 'details'),
            }),
        )

        # Add service-specific fields based on service type
        if obj and obj.service_type:
            service_fields = {
                'cleaning': ('cleaning_option',),
                'maintenance': ('maintenance_option',),
                'gardening': ('gardening_option',),
                'automation': ('automation_option',),
                'security': ('security_option',),
                'cooking': ('cooking_option',),
            }
            if obj.service_type in service_fields:
                fieldsets += (
                    ('Service-Specific Details', {
                        'fields': service_fields[obj.service_type],
                        'description': 'Select the specific service option based on the service type'
                    }),
                )

        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.service_type:
            # Hide all service-specific fields except the one matching the service type
            service_fields = {
                'cleaning': ['maintenance_option', 'gardening_option', 'automation_option', 'security_option', 'cooking_option'],
                'maintenance': ['cleaning_option', 'gardening_option', 'automation_option', 'security_option', 'cooking_option'],
                'gardening': ['cleaning_option', 'maintenance_option', 'automation_option', 'security_option', 'cooking_option'],
                'automation': ['cleaning_option', 'maintenance_option', 'gardening_option', 'security_option', 'cooking_option'],
                'security': ['cleaning_option', 'maintenance_option', 'gardening_option', 'automation_option', 'cooking_option'],
                'cooking': ['cleaning_option', 'maintenance_option', 'gardening_option', 'automation_option', 'security_option'],
            }
            if obj.service_type in service_fields:
                for field in service_fields[obj.service_type]:
                    if field in form.base_fields:
                        form.base_fields[field].widget = form.base_fields[field].hidden_widget()
        return form

    class Media:
        js = ('admin/js/service_admin.js',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'booking', 'grand_total', 'created_at')
    search_fields = ('invoice_number', 'booking__id')
    readonly_fields = ('created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'user', 'provider', 'booking', 'is_read', 'created_at')
    list_filter = ('is_read', 'notification_type', 'created_at')
    search_fields = ('title', 'message', 'user__name', 'provider__name')
    readonly_fields = ('created_at',)


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'created_at')
    search_fields = ('booking__id', 'booking__user__name')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender_type', 'content_preview', 'is_read', 'created_at')
    list_filter = ('sender_type', 'is_read')

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = 'Message'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__name', 'service__name')


@admin.register(ProviderTimeSlot)
class ProviderTimeSlotAdmin(admin.ModelAdmin):
    list_display = ('provider', 'date', 'time', 'status')
    list_filter = ('status', 'date')
    search_fields = ('provider__name',)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'service_type', 'name', 'date', 'time', 'price', 'status')
    list_filter = ('service_type', 'status')
    search_fields = ('service_name', 'name', 'email', 'phone')
    ordering = ('-created_at',)
    list_per_page = 50

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Service Information', {
                'fields': ('service_type', 'service_name', 'description', 'price')
            }),
            ('User Details', {
                'fields': ('user', 'name', 'email', 'phone', 'address')
            }),
            ('Booking Details', {
                'fields': ('date', 'time', 'status')
            }),
        )

        # Add service-specific fields based on service type
        if obj and obj.service_type:

            service_fields = {
                'cleaning': {
                    'option_field': 'cleaning_option',
                    'fields': ('area_size', 'cleaning_frequency', 'special_requirements'),
                    'description': 'Cleaning service specific details'
                },
                'maintenance': {
                    'option_field': 'maintenance_option',
                    'fields': ('maintenance_type', 'equipment_age', 'urgency_level'),
                    'description': 'Maintenance service specific details'
                },
                'garden': {
                    'option_field': 'gardening_option',
                    'fields': ('garden_size', 'service_frequency', 'garden_type'),
                    'description': 'Garden service specific details'
                },
                'home_appliance': {
                    'option_field': 'automation_option',
                    'fields': ('appliance_type', 'brand', 'model', 'issue_description'),
                    'description': 'Home appliance service specific details'
                },
                'security': {
                    'option_field': 'security_option',
                    'fields': ('security_system_type', 'property_size', 'existing_equipment'),
                    'description': 'Security service specific details'
                },
                'food': {
                    'option_field': 'cooking_option',
                    'fields': ('meal_type', 'cuisine', 'dietary_restrictions', 'number_of_people'),
                    'description': 'Food service specific details'
                },
            }

            if obj.service_type in service_fields:
                option_field = service_fields[obj.service_type]['option_field']
                fieldsets += (
                    ('Service-Specific Details', {
                        'fields': (option_field,) + service_fields[obj.service_type]['fields'],
                        'description': service_fields[obj.service_type]['description'],
                        'classes': ('collapse',)
                    }),
                )

        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Add dynamic help text based on service type
        if obj and hasattr(form.base_fields, 'price'):
            if obj.service_type == 'cleaning':
                form.base_fields['price'].help_text = 'Standard cleaning rate is ₹1,500.00'
            elif obj.service_type == 'maintenance':
                form.base_fields['price'].help_text = 'Standard maintenance rate is ₹2,000.00'
            elif obj.service_type == 'garden':
                form.base_fields['price'].help_text = 'Standard gardening rate is ₹1,200.00'
            elif obj.service_type == 'home_appliance':
                form.base_fields['price'].help_text = 'Standard appliance service rate is ₹1,800.00'
            elif obj.service_type == 'security':
                form.base_fields['price'].help_text = 'Standard security service rate is ₹2,500.00'
            elif obj.service_type == 'food':
                form.base_fields['price'].help_text = 'Standard food service rate is ₹1,000.00'

        return form
