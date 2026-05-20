
from django.urls import path
from .views import download_pdf_receipt, download_receipt, payment_checkout, payment_list

urlpatterns = [
    path('', payment_list, name='payment_list'),
    path('checkout/', payment_checkout, name='payment_checkout'),
    path('receipt/<int:payment_id>/download/', download_receipt, name='download_receipt'),
    path('receipt/<int:payment_id>/download-pdf/', download_pdf_receipt, name='download_pdf_receipt'),
]
