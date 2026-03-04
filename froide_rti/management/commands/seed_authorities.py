"""
Management command to seed Indian public authorities.
Usage: python manage.py seed_authorities
       python manage.py seed_authorities --clear
"""
import json
import os
from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = "Seed Indian public authorities from data/authorities_seed.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing IndianPublicAuthority records before seeding",
        )
        parser.add_argument(
            "--file",
            type=str,
            default="data/authorities_seed.json",
            help="Path to seed data JSON file",
        )

    def handle(self, *args, **options):
        from publicbody.models import PublicBody, Jurisdiction, Classification
        from froide_rti.models import IndianPublicAuthority

        seed_file = options["file"]
        if not os.path.exists(seed_file):
            self.stderr.write(self.style.ERROR(f"Seed file not found: {seed_file}"))
            return

        if options["clear"]:
            count, _ = IndianPublicAuthority.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {count} existing records"))

        with open(seed_file, encoding="utf-8") as f:
            authorities = json.load(f)

        # Get or create default jurisdiction and classification
        jurisdiction, _ = Jurisdiction.objects.get_or_create(
            slug="india",
            defaults={"name": "India", "rank": 1, "hidden": False},
        )
        classification, _ = Classification.objects.get_or_create(
            slug="government",
            defaults={"name": "Government", "depth": 0},
        )

        created_count = 0
        updated_count = 0

        for data in authorities:
            slug = data.get("slug") or slugify(data["name"])

            public_body, pb_created = PublicBody.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": data["name"],
                    "jurisdiction": jurisdiction,
                    "classification": classification,
                    "email": data.get("pio_email", ""),
                    "url": data.get("website", ""),
                    "description": f"Public authority under RTI Act 2005. Type: {data['authority_type']}",
                },
            )

            india_auth, ia_created = IndianPublicAuthority.objects.update_or_create(
                public_body=public_body,
                defaults={
                    "authority_type": data["authority_type"],
                    "state": data["state"],
                    "pio_email": data.get("pio_email", ""),
                    "appellate_authority_name": data.get("appellate_authority", ""),
                    "information_commission": data.get("information_commission", ""),
                    "rti_portal_url": data.get("rti_portal_url", ""),
                    "accepts_online_rti": data.get("accepts_online_rti", False),
                    "name_hi": data.get("name_hi", ""),
                    "is_active": True,
                },
            )

            if ia_created:
                created_count += 1
                self.stdout.write(f"  ✅ Created: {data['name']}")
            else:
                updated_count += 1
                self.stdout.write(f"  🔄 Updated: {data['name']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Created: {created_count}, Updated: {updated_count}"
            )
        )
