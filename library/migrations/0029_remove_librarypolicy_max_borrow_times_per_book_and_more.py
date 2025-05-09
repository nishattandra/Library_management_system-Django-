# Generated by Django 5.1.7 on 2025-04-25 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0028_librarypolicy_book_request_duration_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='librarypolicy',
            name='max_borrow_times_per_book',
        ),
        migrations.AddField(
            model_name='borrowedbook',
            name='renew_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='librarypolicy',
            name='max_renew_times',
            field=models.PositiveIntegerField(default=1, help_text='Maximum times a borrowed book can be renewed'),
        ),
        migrations.AddField(
            model_name='librarypolicy',
            name='renew_duration',
            field=models.PositiveIntegerField(default=7, help_text='Number of days added to the due date when the book is renewed'),
        ),
    ]
