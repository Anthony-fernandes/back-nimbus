from django.db import models
from common.models import BaseModel
from apps.companies.models import Company
from apps.clients.models import Client
from apps.users.models import User

class Project(BaseModel):
    STATUS_CHOICES = [("Planejado","Planejado"),("Em andamento","Em andamento"),("Em risco","Em risco"),("Pausado","Pausado"),("Concluído","Concluído")]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="projects")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="Planejado")
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_projects")
    team = models.ManyToManyField(User, blank=True, related_name="projects")
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    real_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    progress = models.IntegerField(default=0)
    start_at = models.DateField(null=True, blank=True)
    due_at = models.DateField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    checklist = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
