from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FroideRtiConfig(AppConfig):
    name = "froide_rti"
    verbose_name = _("OpenRTI India")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Register Celery tasks
        import froide_rti.tasks  # noqa
