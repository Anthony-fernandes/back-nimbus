from django.db import models
from apps.companies.models import Company
from common.models import BaseModel


class BusinessHours(BaseModel):
    """Horário de funcionamento por dia da semana para cálculo de SLA."""
    WEEKDAY_CHOICES = [
        (0, "Segunda-feira"),
        (1, "Terça-feira"),
        (2, "Quarta-feira"),
        (3, "Quinta-feira"),
        (4, "Sexta-feira"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="business_hours")
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["weekday"]
        unique_together = ("company", "weekday")

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time}-{self.end_time}"


class CompanyHoliday(BaseModel):
    """Feriados da empresa para exclusão do cálculo de SLA."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="holidays")
    date = models.DateField()
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["date"]
        unique_together = ("company", "date")

    def __str__(self):
        return f"{self.date} - {self.name}"
