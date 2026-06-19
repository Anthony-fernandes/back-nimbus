from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates a demo company and admin user for first-time setup"

    def handle(self, *args, **options):
        from apps.companies.models import Company
        from apps.users.models import User

        company, created = Company.objects.get_or_create(
            name="Demo Company",
            defaults={"is_active": True}
        )
        if created:
            self.stdout.write(f"Created company: {company.name}")

        if not User.objects.filter(email="admin@demo.com").exists():
            user = User.objects.create_superuser(
                username="admin",
                email="admin@demo.com",
                password="Admin@123456",
                first_name="Administrador",
                last_name="Demo",
                company=company,
                role="ADMIN",
            )
            self.stdout.write(f"Created admin user: {user.email} / Admin@123456")
        else:
            self.stdout.write("Admin user already exists.")

        self.stdout.write(self.style.SUCCESS("Setup complete!"))
