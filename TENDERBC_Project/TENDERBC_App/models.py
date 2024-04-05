from django.db import models
from django.contrib.auth.models import AbstractUser
import django
from django.utils import timezone
from django.core.exceptions import ValidationError

def get_past_20_years():
    current_year = timezone.now().year
    return [(year, str(year)) for year in range(current_year, current_year - 20, -1)]

class User(AbstractUser):
    # Utype = (('admin','admin'),('company','company'))
    Ctype = (('Indian','Indian'),('Foreign','Foreign'))
    # is_company = models.BooleanField(default=False)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    company_type = models.CharField("Company Type", choices=Ctype, default='Indian', max_length=8)
    regno = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    establishment_year = models.IntegerField("Establishment Year", choices=get_past_20_years(), default=timezone.now().year)

def validate_file_extension(value):
    import os
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension. Supported extension is .pdf')

class Tender(models.Model):
    sts = (('Inactive','Inactive'),('Active','Active'), ('Key Submission', 'Key Submission'), ('Completed','Completed'),('Granted','Granted'))
    title = models.CharField(max_length=100, null=False, blank=False)
    description = models.CharField(max_length=1000, null=False, blank=False)
    document = models.FileField(upload_to='tender documents/', validators=[validate_file_extension])
    # created_date_time = models.DateTimeField(default=django.utils.timezone.now())
    start_date_time = models.DateTimeField("Start")
    end_date_time = models.DateTimeField("End")
    Status = models.CharField("Status", choices=sts, default='Inactive', max_length=15)

class Bid(models.Model):
    sts = (('Submitted','Submitted'),('Accpeted','Accepted'),('Rejected','Rejected'), ('Ignored', 'Ignored'))
    tender = models.ForeignKey(Tender,on_delete=models.CASCADE)
    bidder = models.ForeignKey(User,on_delete=models.CASCADE)
    document = models.FileField(upload_to='Bid documents/', validators=[validate_file_extension])
    Status = models.CharField("Status", choices=sts, default='Submitted', max_length=9)
