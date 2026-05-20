
from django.contrib import admin
from .models import Violation

@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ('violation_type', 'driver', 'vehicle', 'fine_amount', 'status')
    list_filter = ('status', 'violation_type')
    search_fields = (
        'violation_type',
        'driver__first_name',
        'driver__last_name',
        'driver__license_number',
        'vehicle__plate_number',
    )
    list_editable = ('status',)
    actions = ('mark_open', 'mark_settled')

    @admin.action(description='Mark selected violations as Open')
    def mark_open(self, request, queryset):
        updated = queryset.update(status='Open')
        self.message_user(request, f'{updated} violation(s) marked as Open.')

    @admin.action(description='Mark selected violations as Settled')
    def mark_settled(self, request, queryset):
        updated = queryset.update(status='Settled')
        self.message_user(request, f'{updated} violation(s) marked as Settled.')
