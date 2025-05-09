# Generated by Django 5.1.7 on 2025-04-11 21:35

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0014_alter_bookrequest_expire_time'),
    ]

    operations = [
        migrations.RenameField(
            model_name='borrowedbook',
            old_name='return_date',
            new_name='due_date',
        ),
        migrations.AddField(
            model_name='borrowedbook',
            name='actual_return_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='borrowedbook',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='bookrequest',
            name='expire_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 12, 1, 35, 7, 44074, tzinfo=datetime.timezone.utc)),
        ),
    ]
