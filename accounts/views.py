from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from drivers.models import Driver
from payments.models import Payment, TicketReference
from vehicles.models import Vehicle
from violations.models import Violation
from .forms import (
    SignUpForm,
    StaffDriverForm,
    StaffVehicleForm,
    StaffViolationForm,
    UpdateEmailForm,
    UpdateMobileForm,
)


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('payment_list')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def account_settings(request):
    mobile_number = request.session.get('mobile_number')
    return render(request, 'accounts/settings.html', {'mobile_number': mobile_number})


@login_required
def update_email(request):
    if request.method == 'POST':
        form = UpdateEmailForm(request.POST)
        if form.is_valid():
            request.user.email = form.cleaned_data['email']
            request.user.save()
            messages.success(request, 'Email address updated successfully.')
            return redirect('account_settings')
    else:
        form = UpdateEmailForm(initial={'email': request.user.email})

    return render(request, 'accounts/update_email.html', {'form': form})


@login_required
def update_mobile(request):
    if request.method == 'POST':
        form = UpdateMobileForm(request.POST)
        if form.is_valid():
            request.session['mobile_number'] = form.cleaned_data['mobile_number']
            messages.success(request, 'Mobile number saved for this browser session.')
            return redirect('account_settings')
    else:
        form = UpdateMobileForm(initial={'mobile_number': request.session.get('mobile_number', '')})

    return render(request, 'accounts/update_mobile.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_portal(request):
    return render(request, 'accounts/staff_portal.html', _staff_portal_context())


def _staff_portal_context():
    repeat_offenders = (
        Driver.objects.annotate(violation_count=Count('violation'))
        .filter(violation_count__gte=2)
        .order_by('-violation_count', 'last_name', 'first_name')
    )

    return {
        'total_drivers': Driver.objects.count(),
        'total_vehicles': Vehicle.objects.count(),
        'total_violations': Violation.objects.count(),
        'total_payments': Payment.objects.count(),
        'pending_payments': Payment.objects.filter(status='pending').count(),
        'paid_payments': Payment.objects.filter(status='paid').count(),
        'repeat_offenders': repeat_offenders,
        'recent_violations': Violation.objects.select_related('driver', 'vehicle').prefetch_related('ticket_references').order_by('-id')[:15],
        'recent_payments': Payment.objects.select_related('user').order_by('-created_at')[:15],
    }


@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_add_driver(request):
    if request.method == 'POST':
        form = StaffDriverForm(request.POST)
        if form.is_valid():
            driver = form.save()
            messages.success(request, f'Driver record added for {driver.first_name} {driver.last_name}.')
            return redirect('staff_add_driver')

        messages.error(request, 'Driver record was not added. Please check the form details.')
    else:
        form = StaffDriverForm()

    drivers = Driver.objects.annotate(violation_count=Count('violation')).order_by('last_name', 'first_name')
    return render(request, 'accounts/staff_driver_records.html', {'form': form, 'drivers': drivers})


@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_add_vehicle(request):
    if request.method == 'POST':
        form = StaffVehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f'Vehicle record added for plate {vehicle.plate_number}.')
            return redirect('staff_add_vehicle')

        messages.error(request, 'Vehicle record was not added. Please check the form details.')
    else:
        form = StaffVehicleForm()

    vehicles = Vehicle.objects.select_related('driver').order_by('plate_number')
    return render(request, 'accounts/staff_vehicle_records.html', {'form': form, 'vehicles': vehicles})


@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_add_violation(request):
    if request.method == 'POST':
        form = StaffViolationForm(request.POST)
        if form.is_valid():
            violation = form.save()
            ticket_reference = TicketReference.objects.create(violation=violation, issued_by=request.user)
            messages.success(
                request,
                f'Violation record added for {violation.driver}. Ticket reference: {ticket_reference.reference_number}.',
            )
            return redirect('staff_add_violation')

        messages.error(request, 'Violation record was not added. Please check the form details.')
    else:
        form = StaffViolationForm()

    violations = (
        Violation.objects.select_related('driver', 'vehicle')
        .prefetch_related('ticket_references')
        .order_by('-id')
    )
    return render(request, 'accounts/staff_violation_records.html', {'form': form, 'violations': violations})


@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_delete_driver(request, driver_id):
    if request.method == 'POST':
        driver = get_object_or_404(Driver, id=driver_id)
        driver_name = str(driver)
        driver.delete()
        messages.success(request, f'Driver record deleted for {driver_name}.')

    return redirect('staff_add_driver')


@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_delete_vehicle(request, vehicle_id):
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        plate_number = vehicle.plate_number
        vehicle.delete()
        messages.success(request, f'Vehicle record deleted for plate {plate_number}.')

    return redirect('staff_add_vehicle')


@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_delete_violation(request, violation_id):
    if request.method == 'POST':
        violation = get_object_or_404(Violation, id=violation_id)
        violation_name = violation.violation_type
        violation.delete()
        messages.success(request, f'Violation record deleted: {violation_name}.')

    return redirect('staff_add_violation')
