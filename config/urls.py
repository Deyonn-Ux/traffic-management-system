
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.views.generic import TemplateView
from drivers.models import Driver
from payments.models import Payment
from vehicles.models import Vehicle
from violations.models import Violation


def dashboard(request):
    context = {
        'total_drivers': Driver.objects.count(),
        'total_vehicles': Vehicle.objects.count(),
        'total_violations': Violation.objects.count(),
        'total_payments': Payment.objects.count(),
    }
    return render(request, 'dashboard.html', context)

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'service-worker.js',
        TemplateView.as_view(template_name='service-worker.js', content_type='application/javascript'),
        name='service_worker',
    ),
    path('accounts/', include('accounts.urls')),
    path('drivers/', include('drivers.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('violations/', include('violations.urls')),
    path('payments/', include('payments.urls')),
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),
    path('', dashboard, name='dashboard'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
