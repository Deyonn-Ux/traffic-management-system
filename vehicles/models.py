
from django.db import models
from drivers.models import Driver

class Vehicle(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    plate_number = models.CharField(max_length=50)
    vehicle_type = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    def __str__(self):
        return self.plate_number
