# Generated for Provider Management System workflow

from django.db import migrations, models
import django.utils.timezone


def migrate_booking_statuses(apps, schema_editor):
    Booking = apps.get_model('core', 'Booking')
    Booking.objects.filter(status='Pending', provider_id__isnull=False).update(
        status='Provider Assigned'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_review_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='accepted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='booking',
            name='started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(
                choices=[
                    ('Pending', 'Pending'),
                    ('Provider Assigned', 'Provider Assigned'),
                    ('Accepted', 'Accepted'),
                    ('In Progress', 'In Progress'),
                    ('Completed', 'Completed'),
                    ('Cancelled', 'Cancelled'),
                ],
                default='Pending',
                max_length=20,
            ),
        ),
        migrations.RunPython(migrate_booking_statuses, migrations.RunPython.noop),
    ]
