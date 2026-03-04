from django.urls import path
from . import views

app_name = "froide_rti"

urlpatterns = [
    path(
        "request/<int:foirequest_pk>/pay/",
        views.initiate_payment,
        name="initiate-payment",
    ),
    path(
        "payment/verify/",
        views.verify_payment,
        name="verify-payment",
    ),
    path(
        "request/<int:foirequest_pk>/bpl-exemption/",
        views.bpl_exemption,
        name="bpl-exemption",
    ),
]
