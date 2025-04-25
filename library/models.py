import math
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Create your models here.
class Book(models.Model):
    book_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    edition = models.CharField(max_length=50, blank=True)
    publication = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=20, unique=True)
    number_of_copies_available = models.PositiveIntegerField(default=0)
    book_dept = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.title} by {self.author}"
    
    def reduce_copies(self):
        """Decreases available copies by one."""
        if self.number_of_copies_available > 0:
            self.number_of_copies_available -= 1
            self.save()



class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    session = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=15)
    profile_image = models.ImageField(upload_to='student_images/')
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.username
    

    

class BookRequest(models.Model):
    REQUESTED = 'REQUESTED'
    ACCEPTED = 'ACCEPTED'
    DECLINED = 'DECLINED'
    STATUS_CHOICES = [
        (REQUESTED, 'Requested'),
        (ACCEPTED, 'Accepted'),
        (DECLINED, 'Declined'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey('library.Book', on_delete=models.CASCADE)  
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=REQUESTED
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    expire_time = models.DateTimeField(null=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.expire_time:
            policy = LibraryPolicy.objects.first()  # Adjust your query if needed.
            if policy:
                self.expire_time = timezone.now() + timedelta(hours=policy.book_request_duration)
            else:
                self.expire_time = timezone.now() + timedelta(hours=4)  # Fallback value
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.user.email} - {self.book.title} ({self.status})"
    
    
class BorrowedBook(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    

    due_date = models.DateField()  
    actual_return_date = models.DateField(null=True, blank=True) 

    status = models.CharField(
        max_length=20,
        choices=[('Issued', 'Issued'), ('Returned', 'Returned')],
        default='Issued'
    )

    updated_at = models.DateTimeField(auto_now=True)
    penalty = models.PositiveIntegerField(default=0)
    penalty_paid = models.BooleanField(default=False)
    def live_penalty(self):
        if self.status == 'Issued' and self.due_date:
            today = timezone.now().date()
            if today > self.due_date:
                days_late = (today - self.due_date).days
                policy = LibraryPolicy.objects.first()  
                if policy:
                    if policy.penalty_type == 'DAY':
                        unit = 1
                    elif policy.penalty_type == 'WEEK':
                        unit = 7
                    elif policy.penalty_type == 'MONTH':
                        unit = 30
                    elif policy.penalty_type == 'YEAR':
                        unit = 365
                    else:
                        unit = 1
                    penalty_units = math.ceil(days_late / unit)
                    penalty = penalty_units * policy.penalty_amount
                    return penalty
                else:
                    return days_late * 2
        return 0

    def __str__(self):
        return f"{self.book.title} - {self.student.name}"
    
    
class OfflineBookRequest(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    penalty = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.book.title} - {self.student.name} - {self.penalty}"

class LibraryPolicy(models.Model):
    PENALTY_TYPE_CHOICES = [
        ('DAY', 'Per Day'),
        ('WEEK', 'Per Week'),
        ('MONTH', 'Per Month'),
        ('YEAR', 'Per Year'),
    ]

    penalty_type = models.CharField(
        max_length=10,
        choices=PENALTY_TYPE_CHOICES,
        default='WEEK'
    )
    penalty_amount = models.PositiveIntegerField(default=0)
    max_books_per_student = models.PositiveIntegerField(default=3)
    max_borrow_duration = models.PositiveIntegerField(help_text="Maximum number of days a book can be borrowed", default=7)
    book_request_duration = models.PositiveIntegerField(default=4, help_text="Duration in hours for a book request to expire")
    max_renew_times = models.PositiveIntegerField(default=1, help_text="Maximum times a borrowed book can be renewed")
    
    def __str__(self):
        return f"Policy: {self.penalty_type} - {self.penalty_amount} per unit"
    
    