
from django.contrib import admin
from .models import Driver

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'license_number', 'contact_number')
    search_fields = ('first_name', 'last_name', 'license_number', 'contact_number')
    ordering = ('last_name', 'first_name')
