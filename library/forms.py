from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Student

class StaffCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    password = forms.CharField(widget=forms.PasswordInput)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  
        if commit:
            user.save()
        return user
    
    


class StudentRegistrationForm(UserCreationForm):
    student_id = forms.CharField(max_length=20)
    name = forms.CharField(max_length=255)
    department = forms.CharField(max_length=100)
    session = forms.CharField(max_length=100)
    email = forms.EmailField()
    mobile_number = forms.CharField(max_length=15)
    profile_image = forms.ImageField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']