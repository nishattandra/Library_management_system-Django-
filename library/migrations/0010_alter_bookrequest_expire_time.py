# Generated by Django 5.1.7 on 2025-04-11 20:23

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0009_alter_bookrequest_expire_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookrequest',
            name='expire_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 12, 0, 23, 37, 438009, tzinfo=datetime.timezone.utc)),
        ),
    ]
