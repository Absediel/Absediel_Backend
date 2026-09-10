from django.urls import path
from .views import contact_submit, quotation_submit

urlpatterns = [
    path('contact/', contact_submit, name='contact_submit'),
    path('quotation/', quotation_submit, name='quotation_submit'),
]
