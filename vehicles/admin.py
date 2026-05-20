
from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'driver', 'vehicle_type', 'model')
    list_filter = ('vehicle_type',)
    search_fields = ('plate_number', 'model', 'driver__first_name', 'driver__last_name', 'driver__license_number')
    ordering = ('plate_number',)
