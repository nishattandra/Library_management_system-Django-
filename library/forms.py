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

    def save(self, commit=True):
        user = super().save(commit=False)  
        cleaned_data = self.cleaned_data
        print('cleaned data', self.cleaned_data)

        if commit:
            user.save()
        print(">>>> Cleaned Data:", self.cleaned_data)

        if not Student.objects.filter(user=user).exists():
            student = Student(
                user=user,  # Link the user to the student
                student_id=self.cleaned_data['student_id'],
                name=self.cleaned_data['name'],
                department=self.cleaned_data['department'],
                session=self.cleaned_data['session'],
                email=self.cleaned_data['email'],
                mobile_number=self.cleaned_data['mobile_number'],
                profile_image=self.cleaned_data['profile_image'],
        )
            student.save()
            print(">>> Student saved:", student) 
        else:
            print("student already exists for this user.")

        return user    