from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # General paths
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('library_management_system/books/', views.books_home, name='books_home'),

    # Staff dashboard
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),

    # Student staff registration and login
    path('student/register/', views.student_register, name='student_register'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/registration_complete/', views.student_registration_complete, name='student_registration_complete'),
    path('verify_student/<int:student_id>/', views.verify_student, name='verify_student'),
    
    # Student dashboard and subpages
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/borrow_books/', views.borrow_books, name='borrow_books'),
    path('student/return_books/', views.return_books, name='return_books'),
    path('student/profile/', views.profile, name='profile'),

    # Book request logic
    path('books/<int:book_id>/request/', views.request_book, name='request_book'),
    path('staff/requests/', views.requested_books, name='requested_books'),
    path('staff/requests/<int:request_id>/decline/', views.decline_request_view, name='decline_request_view'),
    path('staff/requests/accept_book_request/<int:book_id>/<int:student_id>/', views.accept_book_request, name='accept_book_request'),

    # Staff - offline & issue book
    path('staff/offline_books/', views.staff_offline_books, name='staff_offline_books'),
    path('staff/all_books/', views.all_books, name='all_books'),
    path('staff/issue_book/<int:book_id>/<int:student_id>/', views.issue_book, name='issue_book'),
    path('staff/return_books/<int:student_id>/', views.return_selected_books, name='return_selected_books'),
    path('staff/add_book/', views.add_book, name='add_book'),
    path('staff/books/<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('staff/books/<int:book_id>/delete/', views.delete_book, name='delete_book'),
    path('staff/staff_dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/staff_profile/', views.staff_profile, name='staff_profile'),
    path('staff/reports/', views.reports, name='reports'),
    path('staff/reports/download_books_pdf_report/', views.download_books_pdf_report, name='download_books_pdf_report'),
    path('staff/reports/generate_borrowed_books_report/', views.generate_borrowed_books_report, name='generate_borrowed_books_report'),
    path('staff/reports/department-wise-student-list-report/', views.department_wise_student_list_report, name='department_wise_student_list_report'),
    
    #Download history
    path('student/download_history/', views.download_history_pdf, name='download_history'),
]

# If you're serving media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
