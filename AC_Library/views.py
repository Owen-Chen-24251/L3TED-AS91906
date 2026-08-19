import json  # JSON utilities
from collections import defaultdict  # convenient dict-of-lists for grouping
from datetime import date  # current date utility
from urllib.parse import quote  # URL quoting for redirects
from django.http import JsonResponse  # return JSON responses for AJAX
from django.shortcuts import get_object_or_404, render, redirect  # common shortcut helpers
from django.urls import reverse  # reverse URL names to paths
from django.contrib.auth.hashers import check_password, make_password  # password hashing helpers
from django.contrib import messages  # Django messages framework for flash alerts
from django.core.exceptions import ValidationError  # validation exception
from django.db import transaction  # database transaction helpers
from .forms import ContactForm  # local form for contact page
from .models import Book, Genre, Student, Issue, Return, ReturnRequest  # app models

# Create your views here.
def home(request):  # homepage view that lists all books
    all_books = Book.objects.select_related('genre_id').all().order_by('book_title')  # query all books with genre prefetch
    return render(request, 'home.html', {'books': all_books})  # render template with books

def aboutus(request):  # about/contact page; handles contact form submissions
    if request.method == 'POST':
        form = ContactForm(request.POST)  # bind POST data to form
        if form.is_valid():  # validate form fields
            form.save()  # persistent contact message
            messages.success(request, "Your form has been submitted. The librarian will review it shortly and be in touch.")
            return redirect('aboutus')  # redirect back to avoid resubmission
    else:
        form = ContactForm()  # empty form for GET
    return render(request, 'aboutus.html', {'form': form})  # render about page

def search_suggestions(request):  # AJAX endpoint for search autocomplete
    query = request.GET.get('q', '').strip()  # raw query param
    suggestions = []  # accumulated suggestion dicts

    if query:
        books = Book.objects.select_related('genre_id').filter(
            book_title__icontains=query # case-insensitive title match
        )[:5]  # top 5 matching books
        matching_genres = Genre.objects.filter(genre_name__icontains=query)[:5]  # top genres
        related_genres = Genre.objects.filter(book__book_title__icontains=query).distinct()[:5]  # related genres

        for book in books: # add book suggestions
            suggestions.append({  # add book suggestion
                'type': 'book',
                'label': book.book_title,
                'value': book.book_title,
                'url': f"/books/{book.book_id}/"
            }) # add book suggestion

        seen_genre_ids = set()  # dedupe genres
        for genre in list(matching_genres) + list(related_genres):
            if genre.genre_id in seen_genre_ids:
                continue # skip duplicates
            seen_genre_ids.add(genre.genre_id)
            suggestions.append({  # add genre suggestion
                'type': 'genre', # 
                'label': genre.genre_name,
                'value': genre.genre_name,
                'url': '/books/?q=' + genre.genre_name
            }) # add genre suggestion

    return JsonResponse(suggestions, safe=False)  # return JSON list


def books(request):  # listing page; groups books by genre and supports search
    search_term = request.GET.get('q', '').strip()  # optional search term
    books = Book.objects.select_related('genre_id').all().order_by('genre_id__genre_name', 'book_title')  # base queryset

    if search_term:
        books = books.filter(
            book_title__icontains=search_term
        ) | books.filter(
            book_author__icontains=search_term
        ) | books.filter(
            genre_id__genre_name__icontains=search_term
        )  # combine filters for title/author/genre

    books = books.distinct().order_by('genre_id__genre_name', 'book_title')  # dedupe and order

    books_by_genre = defaultdict(list)  # group books by genre name

    for book in books:
        genre_name = book.genre_id.genre_name if book.genre_id else 'Other'  # fallback
        books_by_genre[genre_name].append(book)  # append to genre bucket

    genre_sections = [  # prepare template structure
        {'name': genre_name, 'books': book_list}
        for genre_name, book_list in books_by_genre.items()
    ]

    return render(request, 'books.html', {'genre_sections': genre_sections, 'search_term': search_term}) 
    # render template with grouped books and search term

def book_detail(request, book_id):  # detail view for a single book
    book = get_object_or_404(Book, book_id=book_id)  # 404 if not found
    similar_books = Book.objects.select_related('genre_id').filter(
        genre_id=book.genre_id
    ).exclude(book_id=book.book_id).order_by('book_title')[:4]  # pick up to 4 similar books
    return render(request, 'book_detail.html', {'book': book, 'similar_books': similar_books})

def register(request):  # registration view for new students
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()  # form field
        last_name = request.POST.get('last_name', '').strip()  # form field
        school_email = request.POST.get('school_email', '').strip()  # form field
        password = request.POST.get('password', '')  # form field
        confirm_password = request.POST.get('confirm_password', '')  # form field

        errors = {}  # collect validation errors
        # Validate first name
        if not first_name: 
            errors['first_name'] = ["First name is required."]
        elif not first_name.isalpha():
            errors['first_name'] = ["First name can only contain letters."]
        elif len(first_name) < 3:
            errors['first_name'] = ["First name must be at least 3 characters."]
        elif len(first_name) > 15:
            errors['first_name'] = [f"First name must be 15 characters or fewer. (it has {len(first_name)})"]

        if not last_name:
            errors['last_name'] = ["Last name is required."]
        elif not last_name.isalpha():
            errors['last_name'] = ["Last name can only contain letters."]
        elif len(last_name) < 3:
            errors['last_name'] = ["Last name must be at least 3 characters."]
        elif len(last_name) > 15:
            errors['last_name'] = [f"Last name must be 15 characters or fewer. (it has {len(last_name)})"]
        # Validate school email
        if not school_email:
            errors['school_email'] = ["School email is required."]
        elif not school_email.endswith("@ac.school.nz"):
            errors['school_email'] = ["School email must end with '@ac.school.nz'."]
        # Validate password and confirmation
        if not password:
            errors.setdefault('password', []).append("Password is required.")
        if not confirm_password:
            errors.setdefault('confirm_password', []).append("Please confirm your password.")
        if password and confirm_password and password != confirm_password:
            errors.setdefault('password', []).append("Passwords do not match.")
        if Student.objects.filter(school_email__iexact=school_email).exists():
            errors['school_email'] = ["A user with this school email already exists."]

        if errors:  # render form with errors if validation failed
            return render(request, "register.html", {
                "errors": errors,
                "first_name": first_name,
                "last_name": last_name,
                "school_email": school_email,
            })

        student = Student(
            first_name=first_name,
            last_name=last_name,
            school_email=school_email,
            password=make_password(password),  # hash password
        )
        try:
            student.full_clean()  # model-level validation
            student.save()  # persist student
            messages.success(request, "Registration successful. Please login to continue.")  # success flash
            return redirect("login")
        except ValidationError as e:
            return render(request, "register.html", {
                "errors": e.message_dict,
                "first_name": first_name,
                "last_name": last_name,
                "school_email": school_email,
            }) # render form with model validation errors
    return render(request, "register.html")  # GET: show registration form

def login(request):  # login view handling authentication and session
    if request.session.get('student_id'):
        return redirect('account')  # already logged in

    next_url = request.POST.get('next') or request.GET.get('next', '')  # optional redirect target

    if request.method == "POST":
        school_email = request.POST.get("school_email", "").strip()  # form email
        password = request.POST.get("password", "")  # form password

        errors = {} # collect validation errors
        if not school_email:
            errors['school_email'] = ["School email is required."]
        elif not school_email.endswith("@ac.school.nz"):
            errors['school_email'] = ["School email must end with '@ac.school.nz'."]

        if not password:
            errors['password'] = ["Password is required."]

        if errors:  # validation errors -> re-render form with context
            return render(request, "login.html", {
                "errors": errors,
                "school_email": school_email,
                "next": next_url,
            })

        try: # lookup student by email and verify password
            student = Student.objects.get(school_email__iexact=school_email)  # lookup user
            if check_password(password, student.password):  # verify password
                request.session['student_id'] = student.student_id  # persist login
                request.session['student_name'] = student.first_name
                welcome_message = f"Signed in successfully, welcome {student.first_name}!"
                # Only show a 'successfully signed in' message when user was redirected
                # to login (there is a `next` target). If they visited the login page
                # directly and then navigate elsewhere, avoid showing this message.
                if next_url and next_url.startswith('/'):
                    messages.success(request, welcome_message)
                    return redirect(next_url)
                messages.success(request, welcome_message)
                return redirect('home')
            else: # incorrect password
                return render(request, "login.html", {
                    "error": "Incorrect password. Please try again.",
                    "school_email": school_email,
                    "next": next_url,
                }) # re-render form with error
        except Student.DoesNotExist:
            return render(request, "login.html", {
                "error": "Email is not registered.",
                "school_email": school_email,
                "next": next_url,
            })

    return render(request, "login.html", {"next": next_url})  # GET: show login form

def logout_view(request):  # log the user out by clearing session
    request.session.flush()
    return redirect('home')

def account(request):  # student account dashboard showing loans and history
    student_id = request.session.get('student_id')  # get logged-in student id
    if not student_id:
        return redirect('login')  # require login
    student = Student.objects.filter(student_id=student_id).first()  # fetch student
    if not student:
        request.session.flush()
        return redirect('login')  # invalid session -> force logout
    # Gather issues for this student and separate currently issued vs returned
    issues = Issue.objects.select_related('book_id').filter(student_id=student).order_by('-issue_date')

    current_issues = []  # currently active loans
    past_returns = []  # history of returned loans
    today = date.today()  # reference date

    for issue in issues:
        # Check if this issue has been returned
        returned = Return.objects.filter(issue_id=issue).exists()
        # Check for a pending return request
        pending_request = ReturnRequest.objects.filter(issue_id=issue, processed=False).first() 
        entry = { 
            'issue': issue,
            'book': issue.book_id,
            'issue_date': issue.issue_date,
            'overdue_date': issue.overdue_date,
        } 
        if returned:
            past_returns.append(entry)  # add to returned history
        else:
            # compute days until due (negative if overdue)
            days_until_due = (issue.overdue_date - today).days if issue.overdue_date else None
            entry['days_until_due'] = days_until_due
            entry['is_overdue'] = days_until_due is not None and days_until_due < 0
            entry['days_overdue'] = abs(days_until_due) if days_until_due is not None and days_until_due < 0 else 0
            entry['return_pending'] = bool(pending_request)  # is a return requested?
            entry['pickup_ready'] = bool(issue.pickup_ready)  # waiting for librarian pickup?
            current_issues.append(entry)

    context = {
        'student': student,
        'current_issues': current_issues,
        'past_returns': past_returns,
        'fine_amount': student.fine_amount,
    }
    return render(request, 'account.html', context)  # render account dashboard


def issue_book(request):  # page where students request to issue a book
    student_id = request.session.get('student_id')  # require logged-in student
    if not student_id:
        messages.info(request, 'Please sign in to issue a book.')
        next_url = quote(request.get_full_path(), safe='')  # preserve next target
        return redirect(f"{reverse('login')}?next={next_url}")

    student = get_object_or_404(Student, student_id=student_id)  # get student object
    available_books = Book.objects.filter(book_copies_available__gt=0).order_by('book_title')  # available copies only
    selected_book_id = request.GET.get('book_id')  # optional preselected book
    selected_book = available_books.filter(book_id=selected_book_id).first() if selected_book_id else None

    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        try:
            with transaction.atomic():
                # Lock the book row so simultaneous requests cannot reserve the same copy.
                selected_book = Book.objects.select_for_update().filter(
                    book_id=book_id,
                    book_copies_available__gt=0,
                ).first()
                if not selected_book:
                    messages.error(request, 'That book is not available to issue right now.')
                    return redirect('issue')

                selected_book.book_copies_available -= 1
                selected_book.save(update_fields=['book_copies_available'])

                issue = Issue(book_id=selected_book, student_id=student, pickup_ready=True)
                issue.full_clean()  # run model validation
                issue.save()  # persist request; approval starts the due date
            messages.success(request, f'You have successfully issued {selected_book.book_title}. It is available for pickup in the library.')
            return redirect('account')
        except ValidationError as e:
            messages.error(request, e.message)
            return redirect('issue')

    return render(request, 'issue.html', {
        'student': student,
        'available_books': available_books,
        'selected_book': selected_book,
        'today': date.today(),
    })


def request_return(request):  # endpoint students use to request a return (POST)
    if request.method != 'POST':
        return redirect('account')  # only accept POST

    student_id = request.session.get('student_id')
    if not student_id:
        messages.info(request, 'Please sign in to request a return.')
        return redirect('login')

    student = get_object_or_404(Student, student_id=student_id)  # current student
    issue_id = request.POST.get('issue_id')  # issue being returned
    issue = get_object_or_404(Issue, issue_id=issue_id)  # validate issue

    # Ensure the issue belongs to the logged-in student
    if issue.student_id != student:
        messages.error(request, "That issue does not belong to you.")
        return redirect('account')

    # already returned?
    if Return.objects.filter(issue_id=issue).exists():
        messages.error(request, "This book has already been returned.")
        return redirect('account')

    # existing pending request?
    if ReturnRequest.objects.filter(issue_id=issue, processed=False).exists():
        messages.info(request, "A return request is already pending for this book.")
        return redirect('account')

    rr = ReturnRequest(issue_id=issue, student_id=student)  # create request
    rr.save()  # persist return request
    messages.success(request, "Return request submitted. A librarian will confirm when they receive the book.")
    return redirect('account')
