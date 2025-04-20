from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Student

@receiver(post_save, sender=User)
def create_student_for_new_user(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        Student.objects.get_or_create(user=instance)
