from django.db import models
from django.utils.translation import gettext_lazy as _


class RTIPayment(models.Model):
    """
    Tracks the mandatory ₹10 RTI application fee or BPL exemption.
    RTI Act 2005, Section 6(1): Fee of ₹10 required with application.
    """

    PAYMENT_METHOD_CHOICES = [
        ("razorpay", _("Razorpay (Online)")),
        ("dd", _("Demand Draft")),
        ("ipo", _("Indian Postal Order")),
        ("cash", _("Cash")),
        ("bpl_exempt", _("BPL Exemption")),
    ]

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
        ("refunded", _("Refunded")),
        ("exempt", _("Exempt (BPL)")),
    ]

    foirequest = models.OneToOneField(
        "foirequest.FoiRequest",
        on_delete=models.CASCADE,
        related_name="rti_payment",
        verbose_name=_("RTI Request"),
    )
    amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=10.00,
        verbose_name=_("Amount (₹)"),
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="razorpay",
        verbose_name=_("Payment Method"),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Status"),
    )
    razorpay_order_id = models.CharField(
        max_length=100, blank=True, verbose_name=_("Razorpay Order ID")
    )
    razorpay_payment_id = models.CharField(
        max_length=100, blank=True, verbose_name=_("Razorpay Payment ID")
    )
    razorpay_signature = models.CharField(
        max_length=200, blank=True, verbose_name=_("Razorpay Signature")
    )
    is_bpl_exempt = models.BooleanField(
        default=False, verbose_name=_("BPL Exemption")
    )
    bpl_certificate_number = models.CharField(
        max_length=100, blank=True, verbose_name=_("BPL Certificate Number")
    )
    bpl_certificate_file = models.FileField(
        upload_to="bpl_certificates/",
        blank=True,
        null=True,
        verbose_name=_("BPL Certificate"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("RTI Payment")
        verbose_name_plural = _("RTI Payments")

    def __str__(self):
        if self.is_bpl_exempt:
            return f"BPL Exempt — {self.foirequest}"
        return f"₹{self.amount} ({self.get_status_display()}) — {self.foirequest}"
