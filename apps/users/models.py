from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.companies.models import Company
from common.models import BaseModel

class User(AbstractUser):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("MANAGER", "Manager"),
        ("TECHNICIAN", "Technician"),
        ("CLIENT", "Client"),
    ]
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="ADMIN")
    job_title = models.CharField(max_length=120, blank=True, default="")
    specialty = models.CharField(max_length=120, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    total_hours = models.PositiveIntegerField(default=40)
    used_hours = models.PositiveIntegerField(default=0)
    hourly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    technical_group = models.CharField(max_length=120, blank=True, default="")
    permissions_json = models.JSONField(default=list, blank=True)

    @property
    def full_name_or_username(self):
        return self.get_full_name() or self.username or self.email
