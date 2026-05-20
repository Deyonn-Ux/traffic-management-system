
from django.urls import path
from .views import driver_list

urlpatterns = [
    path('', driver_list, name='driver_list'),
]
