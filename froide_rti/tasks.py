from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


@shared_task(name="froide_rti.check_deadlines")
def check_deadlines():
    """
    Daily task to check RTI deadlines and send reminder emails.
    Run via Celery beat: every day at 9 AM IST.
    """
    from .models import RTIDeadline

    today = timezone.now().date()
    checked = 0
    reminded = 0

    pending_deadlines = RTIDeadline.objects.filter(status="pending").select_related(
        "foirequest__user"
    )

    for deadline in pending_deadlines:
        days_left = (deadline.due_date - today).days
        user = deadline.foirequest.user
        checked += 1

        # Mark overdue
        if days_left < 0 and not deadline.overdue_notice_sent:
            deadline.status = "overdue"
            deadline.overdue_notice_sent = True
            deadline.save()
            _send_deadline_email(
                user=user,
                foirequest=deadline.foirequest,
                subject=str(_("Your RTI request is overdue")),
                message=_overdue_message(deadline),
            )
            reminded += 1

        # 7-day reminder
        elif days_left == 7 and not deadline.reminder_sent_7d:
            deadline.reminder_sent_7d = True
            deadline.save()
            _send_deadline_email(
                user=user,
                foirequest=deadline.foirequest,
                subject=str(_("RTI Reminder: 7 days left for response")),
                message=_reminder_message(deadline, days_left),
            )
            reminded += 1

        # 1-day reminder
        elif days_left == 1 and not deadline.reminder_sent_1d:
            deadline.reminder_sent_1d = True
            deadline.save()
            _send_deadline_email(
                user=user,
                foirequest=deadline.foirequest,
                subject=str(_("RTI Reminder: Response due tomorrow")),
                message=_reminder_message(deadline, days_left),
            )
            reminded += 1

    logger.info(f"Deadline check: {checked} checked, {reminded} reminders sent")
    return {"checked": checked, "reminded": reminded}


@shared_task(name="froide_rti.send_deadline_summary")
def send_weekly_summary():
    """
    Weekly summary of pending RTI requests for each user.
    """
    from .models import RTIDeadline
    from django.contrib.auth import get_user_model

    User = get_user_model()
    today = timezone.now().date()

    users_with_pending = (
        RTIDeadline.objects.filter(status="pending")
        .values_list("foirequest__user", flat=True)
        .distinct()
    )

    for user_id in users_with_pending:
        try:
            user = User.objects.get(pk=user_id)
            deadlines = RTIDeadline.objects.filter(
                status="pending", foirequest__user=user
            ).order_by("due_date")

            if deadlines.exists():
                _send_weekly_summary_email(user, deadlines, today)
        except User.DoesNotExist:
            pass


def _send_deadline_email(user, foirequest, subject, message):
    """Send deadline notification email."""
    if not user.email:
        return
    try:
        send_mail(
            subject=f"[OpenRTI India] {subject}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send deadline email to {user.email}: {e}")


def _reminder_message(deadline, days_left):
    return (
        f"Your RTI request '{deadline.foirequest}' has {days_left} day(s) remaining "
        f"for a response.\n\n"
        f"Deadline type: {deadline.get_deadline_type_display()}\n"
        f"Due date: {deadline.due_date}\n\n"
        f"If you do not receive a response by the due date, you can file a First Appeal "
        f"under Section 19(1) of the RTI Act 2005.\n\n"
        f"— OpenRTI India"
    )


def _overdue_message(deadline):
    return (
        f"Your RTI request '{deadline.foirequest}' is now overdue.\n\n"
        f"The public authority was required to respond by {deadline.due_date}.\n\n"
        f"You can now file a First Appeal under Section 19(1) of the RTI Act 2005.\n"
        f"Visit your request page to file an appeal.\n\n"
        f"— OpenRTI India"
    )


def _send_weekly_summary_email(user, deadlines, today):
    lines = [f"Your pending RTI requests as of {today}:\n"]
    for d in deadlines:
        days = (d.due_date - today).days
        status = f"{days} days left" if days >= 0 else f"OVERDUE by {abs(days)} days"
        lines.append(f"  • {d.foirequest} — {d.get_deadline_type_display()} — {status}")

    message = "\n".join(lines) + "\n\n— OpenRTI India"
    _send_deadline_email(
        user=user,
        foirequest=None,
        subject="Weekly RTI Status Summary",
        message=message,
    )
