
import secrets

from django.db import models
from django.conf import settings
from django.utils import timezone
from violations.models import Violation


class TicketReference(models.Model):
    reference_number = models.CharField(max_length=32, unique=True, blank=True, db_index=True)
    violation = models.ForeignKey(Violation, on_delete=models.CASCADE, related_name='ticket_references')
    is_active = models.BooleanField(default=True)
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        plate_number = self.violation.vehicle.plate_number if self.violation_id else 'No plate'
        return f'{self.reference_number} - {plate_number}'

    def save(self, *args, **kwargs):
        if not self.reference_number:
            year = timezone.now().year
            while True:
                candidate = f'TVS-{year}-{secrets.token_hex(3).upper()}'
                if not TicketReference.objects.filter(reference_number=candidate).exists():
                    self.reference_number = candidate
                    break
        self.reference_number = self.reference_number.strip().upper()
        super().save(*args, **kwargs)


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    violation = models.ForeignKey(Violation, on_delete=models.SET_NULL, null=True, blank=True)
    ticket_reference = models.ForeignKey(TicketReference, on_delete=models.SET_NULL, null=True, blank=True)
    ticket_number = models.CharField(max_length=100, blank=True)
    plate_number = models.CharField(max_length=50, blank=True)
    violation_type = models.CharField(max_length=200, blank=True)
    payment_method = models.CharField(max_length=50)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    receipt_number = models.CharField(max_length=100, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.receipt_number or f"{self.payment_method} payment"
