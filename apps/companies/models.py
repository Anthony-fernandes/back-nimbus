from django.db import models
from common.models import BaseModel

class Company(BaseModel):
    USAGE_TYPE_CHOICES = [
        ("interno", "Uso interno"),
        ("prestador", "Prestação de serviço (B2B)"),
        ("hibrido", "Híbrido (interno + clientes)"),
    ]

    name = models.CharField(max_length=255, unique=True)
    document = models.CharField(max_length=40, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    is_active = models.BooleanField(default=True)
    auto_assign = models.BooleanField(default=False)
    usage_type = models.CharField(
        max_length=20,
        choices=USAGE_TYPE_CHOICES,
        default="prestador",
    )
    email_domain = models.CharField(max_length=120, blank=True, default="")
    timezone = models.CharField(max_length=60, blank=True, default="America/Sao_Paulo")
    locale = models.CharField(max_length=20, blank=True, default="pt-BR")
    currency = models.CharField(max_length=10, blank=True, default="BRL")
    logo = models.URLField(blank=True, default="")
    primary_color = models.CharField(max_length=20, blank=True, default="")

    def __str__(self):
        return self.name
