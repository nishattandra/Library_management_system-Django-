from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from datetime import date

from .forms import StudentRegistrationForm
from .models import Book, Student, BookRequest, BorrowedBook
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import BorrowedBook, Student
from django.contrib.auth.decorators import login_required
from django.urls import reverse

# --- General Views ---

def home(request):
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)

    if request.method == 'POST':
        dept = request.POST.get('dept', '')
        search_text = request.POST.get('search', '')
        page = request.POST.get('page', '')
        request.session['dept'] = dept
        request.session['search'] = search_text
        request.session['page'] = page
        return redirect('home')
    else:
        selected_dept = request.session.pop('dept', '')
        search_text = request.session.pop('search', '')
        page_number = request.session.pop('page', '')
        books_list = Book.objects.all().order_by('pk')
        if selected_dept:
            books_list = books_list.filter(book_dept=selected_dept)
        if search_text:
            books_list = books_list.filter(title__icontains=search_text)
        departments = Book.objects.values_list('book_dept', flat=True).distinct()
        paginator = Paginator(books_list, 10)
        page_obj = paginator.get_page(page_number) if page_number else paginator.get_page(1)
        return render(request, 'library_management_system/index.html', {
            'page_obj': page_obj,
            'selected_dept': selected_dept,
            'search_text': search_text,
            'departments': departments,
        })

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                if user.is_staff:
                    login(request, user)
                    return redirect('staff_dashboard')
                else:
                    messages.error(request, "This is not a student account. Only staff can log in.") 
                    return redirect('login')
            else:
                messages.error(request, "Invalid username or password.") 
                return redirect('login') 
        else:
            messages.error(request, "Please enter valid credentials.") 
            return redirect('login')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})



def logout_view(request):
    logout(request)
    return redirect('home')


# Student Registration view
def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()  
                print(f"User {user.username} created successfully")
                messages.success(request, "Registration successful. Please wait for admin approval.")
                return redirect('student_registration_complete')
            except IntegrityError as e:
                if 'library_student.student_id' in str(e):
                    form.add_error('student_id', 'This student ID is already registered. Please choose a unique one.')
                elif 'library_student.email' in str(e):
                    form.add_error('email', 'This email is already registered. Please use a different one.')
                return render(request, 'registration/student_register.html', {'form': form})
        else:
            messages.error(request, f"Form errors: {form.errors}")
            return render(request, 'registration/student_register.html', {'form': form})
    else:
        form = StudentRegistrationForm()
    return render(request, 'registration/student_register.html', {'form': form})

# Student Registration Complete view
def student_registration_complete(request):
    return render(request, 'registration/student_registration_complete.html')

# Student Login view
def student_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                try:
                    student = user.student  # Try to access the related Student object
                except Student.DoesNotExist:
                    messages.error(request, "No student profile associated with this account. Please register.")
                    return redirect('student_register')
                if student.is_verified:
                    login(request, user)
                    return redirect('student_dashboard')
                else:
                    messages.error(request, "Your account is not verified. Please contact an admin.")
                    return redirect('student_login')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please enter valid credentials.")
    else:
        form = AuthenticationForm()
    return render(request, 'registration/student_login.html', {'form': form})



def verify_student(request, student_id):
    student = Student.objects.get(id=student_id)
    student.is_verified = True
    student.save()

    send_mail(
        'Account Verified',
        'Congratulations! Your student account has been verified. You can now log in.',
        'admin123@gmail.com', 
        [student.user.email],
        fail_silently=False,
    )

    messages.success(request, "Student has been verified and notified via email.")
    return redirect('admin_dashboard')

@login_required(login_url='student_login')
def student_dashboard(request):
    student = request.user.student
    borrowed_books_ids = BorrowedBook.objects.filter(student=student, status='Issued').values_list('book__id', flat=True)
    requested_book_ids = BookRequest.objects.filter(user=request.user, status='REQUESTED').values_list('book__id', flat=True)

    selected_dept = request.GET.get('dept', '')
    search_text = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)

    # Fetch book list
    books_list = Book.objects.all().order_by('pk')
    if selected_dept:
        books_list = books_list.filter(book_dept=selected_dept)
    if search_text:
        books_list = books_list.filter(title__icontains=search_text)

    # Pagination
    paginator = Paginator(books_list, 10)
    page_obj = paginator.get_page(page_number)
    return render(request, 'student_dashboard/dashboard.html', {
        'student_name': student.name,
        'borrowed_books_ids': list(borrowed_books_ids),
        'requested_book_ids': list(requested_book_ids),
        'page_obj': page_obj,
        'selected_dept': selected_dept,
        'search_text': search_text,
        'departments': Book.objects.values_list('book_dept', flat=True).distinct(),
    })

@login_required
def borrow_books(request):
    student = get_object_or_404(Student, user=request.user)
    borrowed_books = BorrowedBook.objects.filter(student=student, status='Issued')
    return render(request, 'student_dashboard/borrow_books.html', {'borrowed_books': borrowed_books})

def return_books(request):
    return render(request, 'student_dashboard/return_books.html')

def profile(request):
    return render(request, 'student_dashboard/profile.html')

@login_required(login_url='student_login')
def request_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    student = get_object_or_404(Student, user=request.user)
    if BorrowedBook.objects.filter(book=book, student=student, status='Issued').exists() or \
       BookRequest.objects.filter(book=book, user=request.user, status='REQUESTED').exists():
        return redirect('student_dashboard')
    book.number_of_copies_available -= 1
    book.save()
    BookRequest.objects.create(
        user=request.user,
        book=book,
        status='REQUESTED',
        requested_at=timezone.now(),
        expire_time=timezone.now() + timedelta(hours=4)
    )
    return redirect('student_dashboard')

def is_staff_user(user):
    return user.is_staff

@user_passes_test(is_staff_user, login_url='login')
def requested_books_view(request):
    requests = BookRequest.objects.filter(status='REQUESTED').order_by('-requested_at')
    return render(request, 'staff_dashboard/requested_books.html', {'requests': requests})

@login_required
@user_passes_test(is_staff_user, login_url='login')
def accept_book_request(request, book_id, student_id):
    book = get_object_or_404(Book, id=book_id)
    student = get_object_or_404(Student, id=student_id)

    if BorrowedBook.objects.filter(book=book, student=student, status='Issued').exists():
        messages.warning(request, f"{student.name} has already borrowed '{book.title}'.")
        return redirect('requested_books')

    if book.number_of_copies_available <= 0:
        messages.error(request, f"No copies of '{book.title}' available.")
        return redirect('requested_books')

    book_request = BookRequest.objects.filter(book=book, user=student.user, status='REQUESTED').first()
    if not book_request:
        messages.warning(request, "This request has already been processed.")
        return redirect('requested_books')

    BorrowedBook.objects.create(
        book=book,
        student=student,
        issue_date=timezone.now().date(),
        due_date=timezone.now().date() + timedelta(days=7),
        status='Issued'
    )

    book.save()

    book_request.status = 'ACCEPTED'
    book_request.save()

    messages.success(request, f"Book '{book.title}' issued to {student.name}.")
    return redirect('requested_books')

@user_passes_test(is_staff_user, login_url='login')
def decline_request_view(request, request_id):
    book_request = get_object_or_404(BookRequest, id=request_id)
    book_request.status = 'DECLINED'
    book_request.save()
    book = book_request.book
    book.number_of_copies_available += 1
    book.save()
    messages.info(request, f"Request for '{book.title}' has been declined.")
    return redirect('requested_books')

@user_passes_test(is_staff_user, login_url='login')
def staff_offline_books(request):
    student_id_query = request.GET.get('student_id', '')
    selected_dept = request.GET.get('dept', '')
    search_text = request.GET.get('search', '')
    student = None
    borrowed_books = []
    borrowed_books_ids = []
    

    if student_id_query:
        try:
            student = Student.objects.get(student_id=student_id_query)
            borrowed_books = BorrowedBook.objects.filter(student=student, status='Issued')

            today = date.today()
            for b in borrowed_books:
                if b.due_date and today > b.due_date:
                    b.live_penalty = (today - b.due_date).days * 2 
                else:
                    b.live_penalty = 0
            borrowed_books_ids = borrowed_books.values_list('book_id', flat=True)
        except Student.DoesNotExist:
            student = None
        
    

    books_list = Book.objects.all().order_by('book_id')
    if selected_dept:
        books_list = books_list.filter(book_dept=selected_dept)
    if search_text:
        books_list = books_list.filter(title__icontains=search_text)

    departments = Book.objects.values_list('book_dept', flat=True).distinct()
    paginator = Paginator(books_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'staff_dashboard/offline_books.html', {
        'student_id_query': student_id_query,
        'student': student,
        'borrowed_books': borrowed_books,
        'page_obj': page_obj,
        'departments': departments,
        'selected_dept': selected_dept,
        'search_text': search_text,
        'borrowed_books_ids': borrowed_books_ids,
    })

@user_passes_test(is_staff_user, login_url='login')
def issue_book(request, book_id, student_id):
    book = get_object_or_404(Book, id=book_id)
    student = get_object_or_404(Student, id=student_id)
    if BorrowedBook.objects.filter(book=book, student=student, status='Issued').exists() or book.number_of_copies_available <= 0:
        return redirect('staff_offline_books')

    BorrowedBook.objects.create(
        book=book,
        student=student,
        issue_date=timezone.now().date(),
        due_date=timezone.now().date() + timedelta(days=14),
        status='Issued'
    )

    book.number_of_copies_available -= 1
    book.save()

    return redirect(request.META.get('HTTP_REFERER', reverse('staff_offline_books')))

@login_required
@user_passes_test(is_staff_user, login_url='login')
def staff_dashboard(request):
    full_name = request.user.get_full_name()
    return render(request, 'staff_dashboard/staff_dashboard.html', {'staff_name': full_name})


@login_required(login_url='student_login')
def profile(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_login')

    return render(request, 'student_dashboard/profile.html', {
        'student': student,
        'email': request.user.email,
    })
    
@user_passes_test(is_staff_user, login_url='login')
def return_selected_books(request, student_id):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_books')
        for borrow_id in selected_ids:
            try:
                borrowed = BorrowedBook.objects.get(id=borrow_id, student__id=student_id, status='Issued')
                borrowed.status = 'Returned'
                borrowed.actual_return_date = timezone.now().date()  
                borrowed.save()

                borrowed.book.number_of_copies_available += 1 
                borrowed.book.save()
            except BorrowedBook.DoesNotExist:
                continue
        messages.success(request, f"{len(selected_ids)} book(s) returned successfully.")
    return redirect('staff_offline_books')

@login_required(login_url='student_login')
def return_books(request):
    student = get_object_or_404(Student, user=request.user)
    returned_books = BorrowedBook.objects.filter(student=student, status='Returned')
    return render(request, 'student_dashboard/return_books.html', {
        'returned_books': returned_books
    })
    
@login_required(login_url='student_login')
def download_history_pdf(request):
    student = request.user.student
    borrowed_books = BorrowedBook.objects.filter(student=student).order_by('-issue_date')

    template_path = 'student_dashboard/pdf_template.html'
    context = {
        'student': student,
        'borrowed_books': borrowed_books
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.student_id}_history.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response
    
    
    
