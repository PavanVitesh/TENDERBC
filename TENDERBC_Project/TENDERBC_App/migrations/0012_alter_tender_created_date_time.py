# Generated by Django 5.0.3 on 2024-03-22 08:32

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TENDERBC_App', '0011_rename_teneder_bid_tender_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tender',
            name='created_date_time',
            field=models.DateTimeField(default=datetime.datetime(2024, 3, 22, 8, 32, 34, 721445, tzinfo=datetime.timezone.utc)),
        ),
    ]