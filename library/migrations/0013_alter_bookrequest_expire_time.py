# Generated by Django 5.1.7 on 2025-04-11 21:17

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0012_alter_bookrequest_expire_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookrequest',
            name='expire_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 12, 1, 17, 9, 5346, tzinfo=datetime.timezone.utc)),
        ),
    ]
