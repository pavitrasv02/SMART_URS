from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.core.management import call_command
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

def trigger_migrate(request):
    call_command('migrate')
    return HttpResponse("Migration done.")

def trigger_collectstatic(request):
    call_command('collectstatic', interactive=False)
    return HttpResponse("Collectstatic done.")

urlpatterns += [
    path('run-migrate/', trigger_migrate),
    path('run-collectstatic/', trigger_collectstatic),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
