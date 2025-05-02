import datetime
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
from datetime import datetime
from django.http import JsonResponse
import json
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .forms import StudentRegistrationForm, BookForm
from .models import Book, LibraryPolicy, Payment, Student, BookRequest, BorrowedBook
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import BorrowedBook, Student
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models.functions import TruncMonth
from django.db.models import Count

# --- General Views ---
def home(request):
    return render(request, 'library_management_system/home.html')

def books_home(request):
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)

    if request.method == 'POST':
        dept = request.POST.get('dept', '')
        search_text = request.POST.get('search', '')
        page = request.POST.get('page', '')
        request.session['dept'] = dept
        request.session['search'] = search_text
        request.session['page'] = page
        return redirect('books_home')
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
        return render(request, 'library_management_system/books.html', {
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



def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                user = form.save()
                print("User created:", user.username)

                print("cleaned_data:", form.cleaned_data)

                student = Student.objects.create(
                    user=user,
                    student_id=form.cleaned_data['student_id'],
                    name=form.cleaned_data['name'],
                    department=form.cleaned_data['department'],
                    session=form.cleaned_data['session'],
                    email=form.cleaned_data['email'],
                    mobile_number=form.cleaned_data['mobile_number'],
                    profile_image=form.cleaned_data['profile_image'],
                )

                print("Student created:", student)

                messages.success(request, "Registration successful. Please wait for admin approval.")
                return redirect('student_registration_complete')
            
            except Exception as e:
                print("Exception during saving student:", e)
                return render(request, 'registration/student_register.html', {'form': form})
        else:
            print("Form is NOT valid.")
            print(form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        print("GET request, rendering empty form.")
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
                    student = user.student 
                except Student.DoesNotExist:
                    messages.error(request, "No student profile associated with this account. Please register.")
                    return redirect('student_login')
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
        'nishattandra2001@gmail.com', 
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
    
    # Get the library policy and max books allowed
    policy = LibraryPolicy.objects.first()
    max_books = policy.max_books_per_student if policy else 3
    
    # Get the current count of borrowed and requested books
    current_count = BorrowedBook.objects.filter(student=request.user.student, status='Issued').count() + \
                    BookRequest.objects.filter(user=request.user, status='REQUESTED').count()

    # Get department and search filter from GET parameters
    selected_dept = request.GET.get('dept', '')
    search_text = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)  # default to 1 if no page is provided

    # Save filters in session for persistent navigation
    request.session['dept'] = selected_dept
    request.session['search'] = search_text

    # Fetch all books and apply filters
    books_list = Book.objects.all().order_by('pk')
    if selected_dept:
        books_list = books_list.filter(book_dept=selected_dept)
    if search_text:
        books_list = books_list.filter(title__icontains=search_text)

    # Get distinct departments for the filter dropdown
    departments = Book.objects.values_list('book_dept', flat=True).distinct()

    # Pagination logic
    paginator = Paginator(books_list, 10)
    page_obj = paginator.get_page(page_number)

    return render(request, 'student_dashboard/dashboard.html', {
        'student_name': student.name,
        'borrowed_books_ids': list(borrowed_books_ids),
        'requested_book_ids': list(requested_book_ids),
        'page_obj': page_obj,
        'selected_dept': selected_dept,
        'search_text': search_text,
        'departments': departments,
        'max_books': max_books,
        'current_count': current_count,
    })


@login_required(login_url='student_login')
def borrow_books(request):
    student = get_object_or_404(Student, user=request.user)
    borrowed_books_list = BorrowedBook.objects.filter(student=student, status='Issued').order_by('-issue_date')
    paginator = Paginator(borrowed_books_list, 5)  # 5 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'student_dashboard/borrow_books.html', {'page_obj': page_obj})


def profile(request):
    return render(request, 'student_dashboard/profile.html')

@login_required(login_url='student_login')

def request_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    student = get_object_or_404(Student, user=request.user)
    policy = LibraryPolicy.objects.first()
    max_books = policy.max_books_per_student if policy else 3

    # Count currently issued books and pending requests for this student.
    current_books_count = BorrowedBook.objects.filter(student=student, status='Issued').count() \
                          + BookRequest.objects.filter(user=request.user, status='REQUESTED').count()

    if current_books_count >= max_books:
        return redirect('student_dashboard')
    
    # Check if the same book is already issued or requested.
    if BorrowedBook.objects.filter(book=book, student=student, status='Issued').exists() or \
       BookRequest.objects.filter(book=book, user=request.user, status='REQUESTED').exists():
        return redirect('student_dashboard')
    
    # Decrement available copies and create book request.
    book.number_of_copies_available -= 1
    book.save()
    BookRequest.objects.create(
        user=request.user,
        book=book,
        status='REQUESTED',
        requested_at=timezone.now(),
        expire_time=timezone.now() + timedelta(hours=policy.book_request_duration if policy else 4)
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

    return redirect('requested_books')

@user_passes_test(is_staff_user, login_url='login')
def decline_request_view(request, request_id):
    book_request = get_object_or_404(BookRequest, id=request_id)
    book_request.status = 'DECLINED'
    book_request.save()
    book = book_request.book
    book.number_of_copies_available += 1
    book.save()
    return redirect('requested_books')

@user_passes_test(is_staff_user, login_url='login')
def staff_offline_books(request):
    student_id_query = request.GET.get('student_id', '')
    selected_dept = request.GET.get('dept', '')
    search_text = request.GET.get('search', '')
    student = None
    borrowed_books = []
    borrowed_books_ids = []
    requested_books = [] 
    current_books_count = 0
    
    policy = LibraryPolicy.objects.first()
    max_books = policy.max_books_per_student if policy else 3
    

    if student_id_query:
        try:
            student = Student.objects.get(student_id=student_id_query, is_verified=True)
            borrowed_books = BorrowedBook.objects.filter(student=student, status='Issued')
            pending_requests = BookRequest.objects.filter(user=student.user, status='REQUESTED')
            requested_books = pending_requests.values_list('book_id', flat=True)
            current_books_count = borrowed_books.count() + pending_requests.count()
            borrowed_books_ids = borrowed_books.values_list('book_id', flat=True)
            today = date.today()
            for b in borrowed_books:
                b.penalty_value = b.live_penalty()  
                b.save()  
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
    
    paginator_history = Paginator(borrowed_books, 5)  # 5 records per page
    history_page_number = request.GET.get('history_page')
    page_obj_history = paginator_history.get_page(history_page_number)

    return render(request, 'staff_dashboard/offline_books.html', {
        'student_id_query': student_id_query,
        'student': student,
        'borrowed_books': borrowed_books,
        'page_obj': page_obj,
        'page_obj_history': page_obj_history,
        'departments': departments,
        'selected_dept': selected_dept,
        'search_text': search_text,
        'borrowed_books_ids': borrowed_books_ids,
        'max_books': max_books,
        'current_books_count': current_books_count,
        'requested_books': requested_books,
    })

@user_passes_test(is_staff_user, login_url='login')
def issue_book(request, book_id, student_id):
    book = get_object_or_404(Book, id=book_id)
    student = get_object_or_404(Student, id=student_id)
    
    policy = LibraryPolicy.objects.first()
    max_books = policy.max_books_per_student if policy else 3
    current_books = BorrowedBook.objects.filter(student=student, status='Issued').count()
    
    
    if current_books >= max_books:
        return redirect('staff_offline_books')

    if BorrowedBook.objects.filter(book=book, student=student, status='Issued').exists() or book.number_of_copies_available <= 0:
        return redirect('staff_offline_books')
    
    max_duration = policy.max_borrow_duration if policy else 7
    BorrowedBook.objects.create(
        book=book,
        student=student,
        issue_date=timezone.now().date(),
        due_date=timezone.now().date() + timedelta(days=max_duration),
        status='Issued'
    )
    book.number_of_copies_available -= 1
    book.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('staff_offline_books')))


@login_required
@user_passes_test(is_staff_user, login_url='login')
def staff_dashboard(request):
    full_name = request.user.first_name + " " + request.user.last_name if request.user.first_name and request.user.last_name else request.user.username
    if request.user.first_name and request.user.last_name:
        full_name = request.user.first_name + " " + request.user.last_name
    else:
        full_name = request.user.username
    print("Staff name:", full_name)
    total_students = Student.objects.filter(is_verified=True).count()
    total_books = Book.objects.count()
    requested_books = BookRequest.objects.filter(status='REQUESTED').count()
    current_year = timezone.now().year

    # Query to get books issued per month
    issued_books_data = (
        BorrowedBook.objects.filter(issue_date__year=current_year)
        .annotate(month=TruncMonth('issue_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    returned_books_data = (
        BorrowedBook.objects.filter(status='Returned', issue_date__year=current_year)
        .annotate(month=TruncMonth('issue_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )


    all_months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    books_issued_dict = {entry['month'].strftime('%B'): entry['count'] for entry in issued_books_data}
    returned_books_dict = {entry['month'].strftime('%B'): entry['count'] for entry in returned_books_data}
    
    books_issued = [books_issued_dict.get(month, 0) for month in all_months]
    books_returned = [returned_books_dict.get(month, 0) for month in all_months]
    
    return render(request, 'staff_dashboard/staff_dashboard.html', {
        'total_students': total_students,
        'total_books': total_books,
        'requested_books': requested_books,
        'staff_name': full_name,
        'months': json.dumps(all_months),
        'books_issued': json.dumps(books_issued),
        'books_returned': json.dumps(books_returned),
    })


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
                borrowed.penalty = borrowed.live_penalty() 
                borrowed.save()

                borrowed.book.number_of_copies_available += 1 
                borrowed.book.save()
            except BorrowedBook.DoesNotExist:
                continue
    return redirect(request.META.get('HTTP_REFERER', reverse('staff_offline_books')))

@login_required(login_url='student_login')
def return_books(request):
    student = get_object_or_404(Student, user=request.user)
    returned_books_list = BorrowedBook.objects.filter(student=student, status='Returned').order_by('-issue_date')
    paginator = Paginator(returned_books_list, 5)  # 5 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'student_dashboard/return_books.html', {'page_obj': page_obj})

    

@user_passes_test(is_staff_user, login_url='login')
def all_books(request):
    if request.method == 'POST':
        dept = request.POST.get('dept', '')
        search_text = request.POST.get('search', '')
        page = request.POST.get('page', '')
        request.session['dept'] = dept
        request.session['search'] = search_text
        request.session['page'] = page
        return redirect('all_books')
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
        return render(request, 'staff_dashboard/all_books.html', {
            'page_obj': page_obj,
            'selected_dept': selected_dept,
            'search_text': search_text,
            'departments': departments,
        })
    
    
#Add new books
@user_passes_test(is_staff_user, login_url='login')  # Only allow staff to add books
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()  
            messages.success(request, "Successfully added books")
            return redirect('all_books')  # Redirect to all books page after saving the book
    else:
        form = BookForm()
    
    return render(request, 'staff_dashboard/all_books.html', {'form': form})



# Edit Book
@user_passes_test(is_staff_user, login_url='login')  # Only staff can edit
def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        # Handle the form submission to save the updated book details
        book.title = request.POST.get('title', book.title)
        book.author = request.POST.get('author', book.author)
        book.edition = request.POST.get('edition', book.edition)
        book.isbn = request.POST.get('isbn', book.isbn)
        book.number_of_copies_available = int(request.POST.get('number_of_copies_available', book.number_of_copies_available))
        book.book_dept = request.POST.get('book_dept', book.book_dept)
        book.publication = request.POST.get('publication', book.publication)
        
        # Save the book object
        book.save()
        print("Book updated:", book.title)
        return JsonResponse({'success': True})
    
    # For GET method, return the book data as JSON for modal
    elif request.method == 'GET':
        return JsonResponse({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'edition': book.edition,
            'isbn': book.isbn,
            'number_of_copies_available': book.number_of_copies_available,
            'book_dept': book.book_dept,
            'publication': book.publication,
        })
    else:
        return redirect('all_books')



#delete books
@user_passes_test(is_staff_user, login_url='login')  # Only allow staff to delete books
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)  
    book.delete()  
    return redirect('all_books')  

def staff_profile(request):
    staff = request.user
    context = {
        'staff': staff
    }
    return render(request, 'staff_dashboard/staff_profile.html', context)


def requested_books(request):
    requests_qs = BookRequest.objects.filter(status='REQUESTED').order_by('-requested_at')
    policy = LibraryPolicy.objects.first()
    now = timezone.now()
    
    for req in requests_qs:
        if req.expire_time and req.expire_time < now and req.status != 'DECLINED':
            req.status = 'DECLINED'
            req.save()

            book = req.book
            book.number_of_copies_available += 1
            book.save()

    
    paginator = Paginator(requests_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'policy': policy,
        'now': now,  
        'page_obj': page_obj,
        'requests': requests_qs,
    }
    return render(request, 'staff_dashboard/requested_books.html', context)


@receiver(pre_save, sender=BorrowedBook)
def create_payment_record(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        previous = BorrowedBook.objects.get(pk=instance.pk)
    except BorrowedBook.DoesNotExist:
        return

    # Check if penalty_paid is changing from False to True
    if not previous.penalty_paid and instance.penalty_paid:
        penalty_amt = instance.live_penalty()
        if penalty_amt > 0 and not Payment.objects.filter(borrowed_book=instance).exists():
            Payment.objects.create(
                student=instance.student,
                borrowed_book=instance,
                penalty_amount=penalty_amt
            )
    
def reports(request):
    # Get the unique departments from the Book model
    departments = Book.objects.values_list('book_dept', flat=True).distinct()
    selected_dept = request.POST.get('department', '')  # Get the selected department from the form

    student_departments = Student.objects.values_list('department', flat=True).distinct()

    # Render the reports page with departments, selected department, and grouped students
    return render(request, 'staff_dashboard/reports.html', {
        'departments': departments,
        'selected_dept': selected_dept,
        'student_departments': student_departments  # Pass the department-wise students to the template
    })

    
def download_books_pdf_report(request):
    departments = Book.objects.values_list('book_dept', flat=True).distinct()  # Get unique department names
    selected_dept = request.POST.get('department', '')  # Get the selected department from the form

    # Filter books by department if a department is selected, otherwise fetch all books
    if selected_dept:
        books = Book.objects.filter(book_dept=selected_dept)
    else:
        books = Book.objects.all()

    # Generate the PDF report when the form is submitted (POST request)
    template_path = 'report_generate/all_books_report.html'  # Path to the HTML template for the PDF
    context = {
        'books': books,
        'department': selected_dept if selected_dept else 'All Departments',
    }

    # Render the HTML content with context
    template = get_template(template_path)
    html = template.render(context)

    # Create a PDF from the HTML content
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{selected_dept if selected_dept else "all_departments"}_books_report.pdf"'

    # Create the PDF from the HTML
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    # Return the generated PDF
    return response

    
    

def generate_borrowed_books_report(request):
    department_filter = request.POST.get('department', '')
    
    # Query borrowed books and include related student info, and filter by department if provided
    borrowed_books = BorrowedBook.objects.filter(status='Issued').select_related('student', 'book')

    if department_filter:
        borrowed_books = borrowed_books.filter(book__book_dept=department_filter)

    # Generate the PDF with the borrowed books and student information
    template = get_template('report_generate/borrowed_books_report.html')
    context = {
        'borrowed_books': borrowed_books,
        'department_filter': department_filter,
    }

    html = template.render(context)

    # Create PDF from HTML
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{department_filter if department_filter else "all_departments"}_borrowed_books_report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    # Return the generated PDF
    return response


def department_wise_student_list_report(request):
    selected_dept = request.POST.get('department', '')

    if selected_dept:
        students = Student.objects.filter(department=selected_dept)
    else:
        students = Student.objects.all()

    context = {
        'students': students,
        'department': selected_dept if selected_dept else 'All Departments',
    }

    template = get_template('report_generate/department_wise_student_list_report.html')
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="department_wise_student_list_{selected_dept if selected_dept else "all_departments"}.pdf"'

    # Generate the PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    return response


def student_reports(request):
    return render(request, 'student_dashboard/student_report.html')



def borrowed_books_report(request):
    user = request.user

    # Get the date filters from the form
    start_date = request.POST.get('start_date', None)
    end_date = request.POST.get('end_date', None)

    # Convert string dates to datetime objects
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Fetch the student's borrowed books
    borrowed_books = BorrowedBook.objects.filter(student__user=user)

    # Apply date filters if provided
    if start_date:
        borrowed_books = borrowed_books.filter(issue_date__gte=start_date)  # Filter by start date (issue date)
    if end_date:
        borrowed_books = borrowed_books.filter(issue_date__lte=end_date)  # Filter by end date (issue date)

    # Prepare the context for the report
    context = {
        'borrowed_books': borrowed_books,
        'student': user.student,  # Assuming the 'Student' model is linked to the User model
        'start_date': start_date,
        'end_date': end_date,
    }

    # Render the HTML template for the report
    template = get_template('report_generate/student_borrowed_books_report.html')
    html = template.render(context)

    # Create PDF from HTML content
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="student_borrowed_books_report.pdf"'

    # Generate the PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    return response

def student_returned_books_report(request):
    user = request.user

    start_date = request.POST.get('start_date', None)
    end_date = request.POST.get('end_date', None)

    # Convert string dates to datetime objects if they are provided
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()  # Use datetime.strptime
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()  # Use datetime.strptime

    # Fetch the student's returned books (filter by status='Returned')
    returned_books = BorrowedBook.objects.filter(student__user=user, status='Returned')

    # Apply date filters if provided
    if start_date:
        returned_books = returned_books.filter(actual_return_date__gte=start_date)  # Filter by start date (return date)
    if end_date:
        returned_books = returned_books.filter(actual_return_date__lte=end_date)  # Filter by end date (return date)

    # Prepare the context for the report
    context = {
        'returned_books': returned_books,
        'student': user.student,  # Assuming the 'Student' model is linked to the User model
        'start_date': start_date,
        'end_date': end_date,
    }

    # Render the HTML template for the report
    template = get_template('report_generate/student_return_books_report.html')
    html = template.render(context)

    # Create PDF from HTML content
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="student_returned_books_report.pdf"'

    # Generate the PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    return response