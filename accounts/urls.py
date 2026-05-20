from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    account_settings,
    signup,
    staff_add_driver,
    staff_add_vehicle,
    staff_add_violation,
    staff_delete_driver,
    staff_delete_vehicle,
    staff_delete_violation,
    staff_portal,
    staff_update_payment_status,
    update_email,
    update_mobile,
)


urlpatterns = [
    path('signup/', signup, name='signup'),
    path('settings/', account_settings, name='account_settings'),
    path('update-email/', update_email, name='update_email'),
    path('update-mobile/', update_mobile, name='update_mobile'),
    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/change_password.html',
        success_url='/accounts/settings/'
    ), name='change_password'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path(
        'staff-login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            extra_context={
                'login_header': 'Staff Login',
                'login_title': 'Staff Login Required',
                'login_message': 'Use your staff account to monitor system activity and manage payments.',
                'staff_login': True,
            },
        ),
        name='staff_login',
    ),
    path('staff-portal/', staff_portal, name='staff_portal'),
    path('add-driver/', staff_add_driver, name='staff_add_driver'),
    path('add-driver/<int:driver_id>/delete/', staff_delete_driver, name='staff_delete_driver'),
    path('add-vehicle/', staff_add_vehicle, name='staff_add_vehicle'),
    path('add-vehicle/<int:vehicle_id>/delete/', staff_delete_vehicle, name='staff_delete_vehicle'),
    path('add-violation/', staff_add_violation, name='staff_add_violation'),
    path('add-violation/<int:violation_id>/delete/', staff_delete_violation, name='staff_delete_violation'),
    path('payments/<int:payment_id>/status/', staff_update_payment_status, name='staff_update_payment_status'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
