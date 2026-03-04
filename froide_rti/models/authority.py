from django.db import models
from django.utils.translation import gettext_lazy as _


INDIAN_STATES = [
    ("AN", "Andaman and Nicobar Islands"),
    ("AP", "Andhra Pradesh"),
    ("AR", "Arunachal Pradesh"),
    ("AS", "Assam"),
    ("BR", "Bihar"),
    ("CH", "Chandigarh"),
    ("CG", "Chhattisgarh"),
    ("DN", "Dadra and Nagar Haveli and Daman and Diu"),
    ("DL", "Delhi"),
    ("GA", "Goa"),
    ("GJ", "Gujarat"),
    ("HR", "Haryana"),
    ("HP", "Himachal Pradesh"),
    ("JK", "Jammu and Kashmir"),
    ("JH", "Jharkhand"),
    ("KA", "Karnataka"),
    ("KL", "Kerala"),
    ("LA", "Ladakh"),
    ("LD", "Lakshadweep"),
    ("MP", "Madhya Pradesh"),
    ("MH", "Maharashtra"),
    ("MN", "Manipur"),
    ("ML", "Meghalaya"),
    ("MZ", "Mizoram"),
    ("NL", "Nagaland"),
    ("OD", "Odisha"),
    ("PY", "Puducherry"),
    ("PB", "Punjab"),
    ("RJ", "Rajasthan"),
    ("SK", "Sikkim"),
    ("TN", "Tamil Nadu"),
    ("TS", "Telangana"),
    ("TR", "Tripura"),
    ("UP", "Uttar Pradesh"),
    ("UK", "Uttarakhand"),
    ("WB", "West Bengal"),
    ("CG_CENTRAL", "Central Government"),
]


class IndianPublicAuthority(models.Model):
    """
    Extends Froide's PublicBody for India-specific RTI authority details.
    Maps to RTI Act 2005, Section 2(h): definition of public authority.
    """

    AUTHORITY_TYPE_CHOICES = [
        ("central_ministry", _("Central Government Ministry")),
        ("central_dept", _("Central Government Department")),
        ("central_psu", _("Central Public Sector Undertaking")),
        ("state_govt", _("State Government")),
        ("state_dept", _("State Government Department")),
        ("state_psu", _("State Public Sector Undertaking")),
        ("local_body", _("Local Body / Municipal Corporation")),
        ("constitutional", _("Constitutional Body")),
        ("statutory", _("Statutory Body")),
        ("aided_body", _("Substantially Aided Body")),
    ]

    public_body = models.OneToOneField(
        "publicbody.PublicBody",
        on_delete=models.CASCADE,
        related_name="india_authority",
        verbose_name=_("Public Body"),
    )
    authority_type = models.CharField(
        max_length=30,
        choices=AUTHORITY_TYPE_CHOICES,
        verbose_name=_("Authority Type"),
    )
    state = models.CharField(
        max_length=20,
        choices=INDIAN_STATES,
        default="CG_CENTRAL",
        verbose_name=_("State / UT"),
    )
    pio_name = models.CharField(
        max_length=255, blank=True, verbose_name=_("Public Information Officer (PIO)")
    )
    pio_email = models.EmailField(blank=True, verbose_name=_("PIO Email"))
    pio_phone = models.CharField(max_length=20, blank=True, verbose_name=_("PIO Phone"))
    pio_address = models.TextField(blank=True, verbose_name=_("PIO Address"))
    appellate_authority_name = models.CharField(
        max_length=255, blank=True, verbose_name=_("First Appellate Authority")
    )
    appellate_authority_email = models.EmailField(
        blank=True, verbose_name=_("Appellate Authority Email")
    )
    information_commission = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Information Commission (Second Appeal)"),
    )
    rti_portal_url = models.URLField(
        blank=True, verbose_name=_("RTI Online Portal URL")
    )
    accepts_online_rti = models.BooleanField(
        default=False, verbose_name=_("Accepts Online RTI")
    )
    accepts_email_rti = models.BooleanField(
        default=False, verbose_name=_("Accepts RTI via Email")
    )
    name_hi = models.CharField(
        max_length=500, blank=True, verbose_name=_("Name (Hindi)")
    )
    last_verified = models.DateField(
        null=True, blank=True, verbose_name=_("Last Verified")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    class Meta:
        verbose_name = _("Indian Public Authority")
        verbose_name_plural = _("Indian Public Authorities")
        ordering = ["state", "authority_type"]

    def __str__(self):
        return f"{self.public_body.name} ({self.get_state_display()})"
