from django.db import models
from django.utils.translation import gettext_lazy as _


class RTIAppeal(models.Model):
    """
    India's two-tier appeal system under RTI Act 2005:
    - First Appeal: Section 19(1) — to First Appellate Authority (senior officer)
    - Second Appeal: Section 19(3) — to Central/State Information Commission
    """

    APPEAL_TYPE_CHOICES = [
        ("first", _("First Appeal — Section 19(1)")),
        ("second", _("Second Appeal — Section 19(3)")),
    ]

    GROUND_CHOICES = [
        ("no_response", _("No Response within 30 days")),
        ("incomplete", _("Incomplete Information Provided")),
        ("incorrect", _("Incorrect Information Provided")),
        ("excessive_fee", _("Excessive Fee Charged")),
        ("wrongful_denial", _("Information Wrongfully Denied")),
        ("third_party", _("Third Party Information Withheld")),
        ("other", _("Other Grounds")),
    ]

    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("filed", _("Filed")),
        ("under_review", _("Under Review")),
        ("hearing_scheduled", _("Hearing Scheduled")),
        ("allowed", _("Allowed")),
        ("partially_allowed", _("Partially Allowed")),
        ("dismissed", _("Dismissed")),
        ("withdrawn", _("Withdrawn")),
    ]

    foirequest = models.ForeignKey(
        "foirequest.FoiRequest",
        on_delete=models.CASCADE,
        related_name="rti_appeals",
        verbose_name=_("RTI Request"),
    )
    appeal_type = models.CharField(
        max_length=10,
        choices=APPEAL_TYPE_CHOICES,
        verbose_name=_("Appeal Type"),
    )
    ground = models.CharField(
        max_length=30,
        choices=GROUND_CHOICES,
        default="no_response",
        verbose_name=_("Ground of Appeal"),
    )
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name=_("Status"),
    )
    filed_date = models.DateField(null=True, blank=True, verbose_name=_("Filed Date"))
    hearing_date = models.DateField(
        null=True, blank=True, verbose_name=_("Hearing Date")
    )
    decision_date = models.DateField(
        null=True, blank=True, verbose_name=_("Decision Date")
    )
    appellate_authority = models.CharField(
        max_length=255, blank=True, verbose_name=_("Appellate Authority")
    )
    registration_number = models.CharField(
        max_length=100, blank=True, verbose_name=_("Registration Number")
    )
    appeal_text = models.TextField(verbose_name=_("Appeal Text"))
    decision_summary = models.TextField(
        blank=True, verbose_name=_("Decision Summary")
    )
    penalty_imposed = models.BooleanField(
        default=False, verbose_name=_("Penalty Imposed on PIO")
    )
    penalty_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Penalty Amount (₹)"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("RTI Appeal")
        verbose_name_plural = _("RTI Appeals")
        ordering = ["-filed_date"]

    def __str__(self):
        return f"{self.get_appeal_type_display()} — {self.foirequest} ({self.get_status_display()})"
