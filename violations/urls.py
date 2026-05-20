
from django.urls import path
from .views import violation_list

urlpatterns = [
    path('', violation_list, name='violation_list'),
]
