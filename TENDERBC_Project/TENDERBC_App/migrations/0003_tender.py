# Generated by Django 4.2.3 on 2024-02-27 10:58

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TENDERBC_App', '0002_alter_user_establishment_year'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=1000)),
                ('document', models.FileField(upload_to='Tender documents/')),
                ('created_date_time', models.DateTimeField(default=datetime.datetime(2024, 2, 27, 10, 58, 49, 191363, tzinfo=datetime.timezone.utc))),
                ('start_date_time', models.DateTimeField(default=datetime.datetime(2024, 2, 27, 10, 58, 49, 191363, tzinfo=datetime.timezone.utc))),
                ('end_date_time', models.DateTimeField()),
            ],
        ),
    ]
