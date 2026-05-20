
from django.db.models import Count
from django.shortcuts import render
from .models import Driver


def mask_word(value):
    value = str(value or '').strip()
    if not value:
        return ''
    visible = 2 if len(value) > 2 else 1
    return value[:visible] + ('*' * max(len(value) - visible, 2))


def mask_name(first_name, last_name):
    return f"{mask_word(first_name)} {mask_word(last_name)}"


def mask_code(value):
    value = str(value or '').strip()
    if len(value) <= 4:
        return mask_word(value)
    return f"{value[:2]}{'*' * max(len(value) - 4, 3)}{value[-2:]}"


def driver_list(request):
    drivers = Driver.objects.annotate(violation_count=Count('violation')).order_by('-violation_count', 'last_name', 'first_name')
    is_staff = request.user.is_authenticated and request.user.is_staff

    for driver in drivers:
        if is_staff:
            driver.display_name = f"{driver.first_name} {driver.last_name}"
            driver.display_license = driver.license_number
            driver.display_contact = driver.contact_number
            driver.display_address = driver.address
        else:
            driver.display_name = mask_name(driver.first_name, driver.last_name)
            driver.display_license = mask_code(driver.license_number)
            driver.display_contact = 'Hidden for privacy'
            driver.display_address = 'Hidden for privacy'

    return render(request, 'drivers/list.html', {'drivers': drivers})
