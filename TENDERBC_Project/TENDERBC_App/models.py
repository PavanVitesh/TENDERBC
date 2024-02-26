from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

def get_past_20_years():
    current_year = timezone.now().year
    return [(year, str(year)) for year in range(current_year, current_year - 20, -1)]

# Create your models here.
class User(AbstractUser):
    # Utype = (('admin','admin'),('company','company'))
    Ctype = (('Indian','Indian'),('Foreign','Foreign'))
    # is_company = models.BooleanField(default=False)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    company_type = models.CharField("Company Type", choices=Ctype, default='Indian', max_length=8)
    regno = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    establishment_year = models.IntegerField("Establishment Year", choices=get_past_20_years(), default=timezone.now().year)