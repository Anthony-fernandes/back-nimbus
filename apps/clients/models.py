from django.db import models

from apps.companies.models import Company
from common.models import BaseModel


class Client(BaseModel):
    ORGANIZATION_TYPE_CHOICES = [
        ("CLIENTE_EMPRESA", "Cliente empresa"),
        ("CLIENTE_PESSOA", "Cliente pessoa"),
        ("EMPRESA_INTERNA", "Empresa interna"),
        ("SETOR_INTERNO", "Setor interno"),
        ("DEPARTAMENTO", "Departamento"),
        ("FILIAL", "Filial"),
        ("OUTRO", "Outro"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="clients")
    name = models.CharField(max_length=255)
    organization_type = models.CharField(
        max_length=40,
        choices=ORGANIZATION_TYPE_CHOICES,
        default="CLIENTE_EMPRESA",
    )
    document = models.CharField(max_length=60, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    sector = models.CharField(max_length=255, blank=True, default="")
    contact_name = models.CharField(max_length=255, blank=True, default="")
    active = models.BooleanField(default=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    plan = models.CharField(max_length=80, blank=True, default="Pro")
    mrr = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    health = models.CharField(max_length=30, blank=True, default="Bom")
    notes = models.TextField(blank=True, default="")
    status = models.CharField(max_length=30, default="Ativo")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
