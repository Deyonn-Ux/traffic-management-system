
from django.shortcuts import render
from .models import Vehicle


def mask_word(value):
    value = str(value or '').strip()
    if not value:
        return ''
    visible = 2 if len(value) > 2 else 1
    return value[:visible] + ('*' * max(len(value) - visible, 2))


def vehicle_list(request):
    vehicles = Vehicle.objects.select_related('driver').order_by('plate_number')
    is_staff = request.user.is_authenticated and request.user.is_staff

    for vehicle in vehicles:
        if is_staff:
            vehicle.display_driver = str(vehicle.driver)
            vehicle.display_plate = vehicle.plate_number
        else:
            vehicle.display_driver = f"{mask_word(vehicle.driver.first_name)} {mask_word(vehicle.driver.last_name)}"
            vehicle.display_plate = vehicle.plate_number

    return render(request, 'vehicles/list.html', {'vehicles': vehicles})
