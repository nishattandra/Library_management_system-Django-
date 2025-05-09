# Generated by Django 5.1.7 on 2025-03-15 17:47

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0004_alter_bookrequest_expire_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookrequest',
            name='expire_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 15, 21, 47, 29, 44587, tzinfo=datetime.timezone.utc)),
        ),
        migrations.CreateModel(
            name='BorrowedBook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issue_date', models.DateField(auto_now_add=True)),
                ('return_date', models.DateField()),
                ('status', models.CharField(choices=[('Issued', 'Issued'), ('Returned', 'Returned')], default='Issued', max_length=20)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.book')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.student')),
            ],
        ),
    ]
