from django.contrib import admin
from django.contrib.auth.models import User
from .forms import StaffCreationForm
from .models import Book
from .models import Student
from django import forms
from .models import BookRequest, BorrowedBook

admin.site.unregister(User)

class StaffAdmin(admin.ModelAdmin):
    add_form = StaffCreationForm
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email')
admin.site.register(User, StaffAdmin)
    
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'department', 'session', 'is_verified')
    search_fields = ('user__username', 'student_id', 'department')

admin.site.register(Student, StudentAdmin)



class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'edition', 'book_dept', 'number_of_copies_available'] 
    search_fields = ['title', 'author']
    list_filter = ['book_dept', 'edition'] 
    

admin.site.register(Book, BookAdmin)



admin.site.register(BookRequest)

@admin.register(BorrowedBook)
class BorrowedBookAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'status', 'issue_date', 'due_date', 'actual_return_date', 'live_penalty')
    list_filter = ('status', 'student', 'book')
    search_fields = ('student__name', 'book__title')
