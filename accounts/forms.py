from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from drivers.models import Driver
from vehicles.models import Vehicle
from violations.models import Violation


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email Address')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class UpdateEmailForm(forms.Form):
    email = forms.EmailField(required=True, label='New Email Address')


class UpdateMobileForm(forms.Form):
    mobile_number = forms.CharField(required=True, max_length=20, label='Mobile Number')


class StaffDriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ('first_name', 'last_name', 'license_number', 'contact_number', 'address')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'License number'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Complete address'}),
        }


class StaffVehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ('driver', 'plate_number', 'vehicle_type', 'model')
        widgets = {
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'plate_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Plate number'}),
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vehicle type'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Model'}),
        }


class StaffViolationForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Settled', 'Settled'),
    ]

    plate_number = forms.ModelChoiceField(
        queryset=Vehicle.objects.none(),
        empty_label='---------',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        initial='Open',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Violation
        fields = ('driver', 'vehicle', 'plate_number', 'violation_type', 'fine_amount', 'status')
        widgets = {
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'violation_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Violation type'}),
            'fine_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Fine amount', 'min': '0', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vehicles = Vehicle.objects.select_related('driver').order_by('model', 'vehicle_type', 'plate_number')
        self.fields['vehicle'].queryset = vehicles
        self.fields['plate_number'].queryset = vehicles.order_by('plate_number')
        self.fields['vehicle'].label_from_instance = (
            lambda vehicle: f'{vehicle.model} - {vehicle.vehicle_type}'
        )
        self.fields['plate_number'].label_from_instance = (
            lambda vehicle: vehicle.plate_number
        )

    def clean(self):
        cleaned_data = super().clean()
        driver = cleaned_data.get('driver')
        vehicle = cleaned_data.get('vehicle')
        plate_number = cleaned_data.get('plate_number')

        if driver and vehicle and vehicle.driver_id != driver.id:
            self.add_error('vehicle', 'Selected vehicle must belong to the selected driver.')

        if vehicle and plate_number and vehicle.id != plate_number.id:
            self.add_error('plate_number', 'Selected plate number must match the selected vehicle.')

        return cleaned_data
