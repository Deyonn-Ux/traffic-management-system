
from django.urls import path
from .views import vehicle_list

urlpatterns = [
    path('', vehicle_list, name='vehicle_list'),
]
