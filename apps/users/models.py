from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.clients.models import Client
from apps.companies.models import Company
from common.models import BaseModel


class User(AbstractUser):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("TECHNICIAN", "Technician"),
        ("CLIENT", "Client"),
    ]

    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name="portal_users")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="ADMIN")
    job_title = models.CharField(max_length=120, blank=True, default="")
    specialty = models.CharField(max_length=120, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    total_hours = models.PositiveIntegerField(default=40)
    used_hours = models.PositiveIntegerField(default=0)
    hourly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    technical_group = models.CharField(max_length=120, blank=True, default="")
    permissions_json = models.JSONField(default=list, blank=True)
    granted_permissions = models.JSONField(default=dict, blank=True)
    denied_permissions = models.JSONField(default=dict, blank=True)
    permission_blocks = models.ManyToManyField(
        "PermissionBlock",
        blank=True,
        related_name="users",
    )

    @property
    def full_name_or_username(self):
        return self.get_full_name() or self.username or self.email


class PermissionBlock(BaseModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="permission_blocks",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    permissions = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


class UserOrganization(BaseModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="user_organization_links",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="organization_links",
    )
    organization = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="user_links",
    )
    role = models.CharField(max_length=60, blank=True, default="")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization__name", "user__username"]
        unique_together = ("user", "organization")

    def __str__(self):
        return f"{self.user.full_name_or_username} -> {self.organization.name}"
