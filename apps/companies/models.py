from django.db import models
from common.models import BaseModel

class Company(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    document = models.CharField(max_length=40, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
