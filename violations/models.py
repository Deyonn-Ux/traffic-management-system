
from django.db import models
from drivers.models import Driver
from vehicles.models import Vehicle

class Violation(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    violation_type = models.CharField(max_length=200)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)

    def __str__(self):
        return self.violation_type
