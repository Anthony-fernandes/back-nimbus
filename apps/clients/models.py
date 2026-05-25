from django.db import models
from common.models import BaseModel
from apps.companies.models import Company

class Client(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="clients")
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    sector = models.CharField(max_length=255, blank=True, default="")
    contact_name = models.CharField(max_length=255, blank=True, default="")
    plan = models.CharField(max_length=80, blank=True, default="Pro")
    mrr = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    health = models.CharField(max_length=30, blank=True, default="Bom")
    notes = models.TextField(blank=True, default="")
    status = models.CharField(max_length=30, default="Ativo")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
