from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta


class RTIDeadline(models.Model):
    """
    Tracks statutory deadlines under RTI Act 2005:
    - Section 7(1): 30 days for normal response
    - Section 7(1) proviso: 48 hours if life/liberty at stake
    - Section 19(1): 30 days for First Appeal
    - Section 19(3): 90 days for Second Appeal to Information Commission
    """

    DEADLINE_TYPE_CHOICES = [
        ("response", _("Initial Response (30 days)")),
        ("urgent", _("Urgent Response — Life/Liberty (48 hours)")),
        ("first_appeal", _("First Appeal (30 days)")),
        ("second_appeal", _("Second Appeal to IC (90 days)")),
    ]

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("responded", _("Responded")),
        ("overdue", _("Overdue")),
        ("extended", _("Extended")),
        ("transferred", _("Transferred to Another PIO")),
    ]

    foirequest = models.ForeignKey(
        "foirequest.FoiRequest",
        on_delete=models.CASCADE,
        related_name="rti_deadlines",
        verbose_name=_("RTI Request"),
    )
    deadline_type = models.CharField(
        max_length=20,
        choices=DEADLINE_TYPE_CHOICES,
        default="response",
        verbose_name=_("Deadline Type"),
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    due_date = models.DateField(verbose_name=_("Due Date"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Status"),
    )
    responded_on = models.DateField(
        null=True, blank=True, verbose_name=_("Responded On")
    )
    reminder_sent_7d = models.BooleanField(
        default=False, verbose_name=_("7-Day Reminder Sent")
    )
    reminder_sent_1d = models.BooleanField(
        default=False, verbose_name=_("1-Day Reminder Sent")
    )
    overdue_notice_sent = models.BooleanField(
        default=False, verbose_name=_("Overdue Notice Sent")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("RTI Deadline")
        verbose_name_plural = _("RTI Deadlines")
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.get_deadline_type_display()} — Due: {self.due_date}"

    @property
    def days_remaining(self):
        return (self.due_date - timezone.now().date()).days

    @property
    def is_overdue(self):
        return self.days_remaining < 0 and self.status == "pending"

    def save(self, *args, **kwargs):
        if not self.due_date:
            days_map = {
                "response": 30,
                "urgent": 2,
                "first_appeal": 30,
                "second_appeal": 90,
            }
            days = days_map.get(self.deadline_type, 30)
            self.due_date = self.start_date + timedelta(days=days)
        super().save(*args, **kwargs)
