# Generated by Django 5.1.7 on 2025-03-12 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('book_id', models.CharField(max_length=20, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('author', models.CharField(max_length=255)),
                ('edition', models.CharField(blank=True, max_length=50)),
                ('publication', models.CharField(blank=True, max_length=255)),
                ('isbn', models.CharField(max_length=20, unique=True)),
                ('number_of_copies_available', models.PositiveIntegerField(default=0)),
                ('book_dept', models.CharField(blank=True, max_length=100)),
            ],
        ),
    ]
