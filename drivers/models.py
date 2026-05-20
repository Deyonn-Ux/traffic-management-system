
from django.db import models

class Driver(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
