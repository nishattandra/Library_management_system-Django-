# Generated by Django 5.1.7 on 2025-04-12 01:05

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0017_borrowedbook_penalty_paid_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookrequest',
            name='expire_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 12, 5, 5, 27, 159610, tzinfo=datetime.timezone.utc)),
        ),
    ]
