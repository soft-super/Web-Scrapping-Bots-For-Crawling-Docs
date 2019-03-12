from django.urls import path

from digital_api.views import DigitalCertificateView

urlpatterns = [
    path('get_signed_key/', DigitalCertificateView.as_view()),
]
