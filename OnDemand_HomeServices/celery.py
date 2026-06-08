"""Celery application for SMART URS background task processing."""

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OnDemand_HomeServices.settings')

app = Celery('OnDemand_HomeServices')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
