
from django.shortcuts import render
from .models import Violation


def mask_word(value):
    value = str(value or '').strip()
    if not value:
        return ''
    visible = 2 if len(value) > 2 else 1
    return value[:visible] + ('*' * max(len(value) - visible, 2))


def violation_list(request):
    plate = request.GET.get('plate', '').strip()
    license_number = request.GET.get('license', '').strip()
    violations = Violation.objects.select_related('driver', 'vehicle')

    if plate:
        violations = violations.filter(vehicle__plate_number__icontains=plate)

    if license_number:
        violations = violations.filter(driver__license_number__icontains=license_number)

    violations = list(violations.order_by('status', 'violation_type'))
    is_staff = request.user.is_authenticated and request.user.is_staff

    for violation in violations:
        if is_staff:
            violation.display_driver = str(violation.driver)
        else:
            violation.display_driver = f"{mask_word(violation.driver.first_name)} {mask_word(violation.driver.last_name)}"

    context = {
        'violations': violations,
        'plate_query': plate,
        'license_query': license_number,
    }
    return render(request, 'violations/list.html', context)
