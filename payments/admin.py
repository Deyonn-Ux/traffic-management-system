
from django.contrib import admin
from django.utils import timezone
from .models import Payment, TicketReference


@admin.register(TicketReference)
class TicketReferenceAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number',
        'plate_number',
        'violation_type',
        'fine_amount',
        'is_active',
        'issued_by',
        'created_at',
    )
    list_filter = ('is_active', 'created_at')
    search_fields = (
        'reference_number',
        'violation__vehicle__plate_number',
        'violation__driver__first_name',
        'violation__driver__last_name',
        'violation__violation_type',
    )
    autocomplete_fields = ('violation', 'issued_by')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_editable = ('is_active',)

    def plate_number(self, obj):
        return obj.violation.vehicle.plate_number

    def violation_type(self, obj):
        return obj.violation.violation_type

    def fine_amount(self, obj):
        return obj.violation.fine_amount


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number',
        'ticket_number',
        'plate_number',
        'ticket_reference',
        'payment_method',
        'amount_paid',
        'status',
        'user',
        'created_at',
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = (
        'receipt_number',
        'ticket_number',
        'plate_number',
        'ticket_reference__reference_number',
        'ticket_reference__violation__vehicle__plate_number',
        'user__username',
    )
    readonly_fields = ('receipt_number', 'created_at')
    autocomplete_fields = ('ticket_reference', 'violation', 'user')
    ordering = ('-created_at',)
    list_editable = ('status',)
    actions = ('mark_as_paid', 'mark_as_pending', 'mark_as_rejected')

    def save_model(self, request, obj, form, change):
        if obj.status in ('paid', 'rejected') and not obj.verified_at:
            obj.verified_at = timezone.now()
        if obj.status == 'pending':
            obj.verified_at = None
        super().save_model(request, obj, form, change)
        if obj.status == 'paid' and obj.violation_id:
            obj.violation.status = 'Settled'
            obj.violation.save(update_fields=['status'])

    @admin.action(description='Mark selected payments as Paid')
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid', verified_at=timezone.now())
        for payment in queryset.select_related('violation'):
            if payment.violation_id:
                payment.violation.status = 'Settled'
                payment.violation.save(update_fields=['status'])
        self.message_user(request, f'{updated} payment(s) marked as Paid.')

    @admin.action(description='Mark selected payments as Pending Verification')
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending', verified_at=None)
        self.message_user(request, f'{updated} payment(s) marked as Pending Verification.')

    @admin.action(description='Mark selected payments as Rejected')
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected', verified_at=timezone.now())
        self.message_user(request, f'{updated} payment(s) marked as Rejected.')
