# Generated by Django 5.0.3 on 2024-03-21 06:19

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TENDERBC_App', '0008_alter_tender_created_date_time_bid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tender',
            name='created_date_time',
            field=models.DateTimeField(default=datetime.datetime(2024, 3, 21, 6, 19, 35, 18406, tzinfo=datetime.timezone.utc)),
        ),
    ]
