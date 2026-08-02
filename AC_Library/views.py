import json
from collections import defaultdict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from django.core.exceptions import ValidationError
from .forms import ContactForm
from .models import Book, Genre, Student

# Create your views here.
def home(request):
    all_books = Book.objects.select_related('genre_id').all().order_by('book_title')
    return render(request, 'home.html', {'books': all_books})

def aboutus(request):
    if request.method == 'POST':
        form = ContactForm(request.POST) # Pass the submitted data to the form
        if form.is_valid():               # Automatically validates field types and constraints
            form.save()                   # Saves the data directly to your database table
            return redirect('aboutus')   # Redirect back to the about page after saving
    else:
        form = ContactForm()             # Provide a blank form for GET requests
    return render(request, 'aboutus.html', {'form': form})

def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []

    if query:
        books = Book.objects.select_related('genre_id').filter(
            book_title__icontains=query
        )[:5]
        matching_genres = Genre.objects.filter(genre_name__icontains=query)[:5]
        related_genres = Genre.objects.filter(book__book_title__icontains=query).distinct()[:5]

        for book in books:
            suggestions.append({
                'type': 'book',
                'label': book.book_title,
                'value': book.book_title,
                'url': f"/books/{book.book_id}/"
            })

        seen_genre_ids = set()
        for genre in list(matching_genres) + list(related_genres):
            if genre.genre_id in seen_genre_ids:
                continue
            seen_genre_ids.add(genre.genre_id)
            suggestions.append({
                'type': 'genre',
                'label': genre.genre_name,
                'value': genre.genre_name,
                'url': '/books/?q=' + genre.genre_name
            })

    return JsonResponse(suggestions, safe=False)


def books(request):
    search_term = request.GET.get('q', '').strip()
    books = Book.objects.select_related('genre_id').all().order_by('genre_id__genre_name', 'book_title')

    if search_term:
        books = books.filter(
            book_title__icontains=search_term
        ) | books.filter(
            book_author__icontains=search_term
        ) | books.filter(
            genre_id__genre_name__icontains=search_term
        )

    books = books.distinct().order_by('genre_id__genre_name', 'book_title')

    books_by_genre = defaultdict(list)

    for book in books:
        genre_name = book.genre_id.genre_name if book.genre_id else 'Other'
        books_by_genre[genre_name].append(book)

    genre_sections = [
        {'name': genre_name, 'books': book_list}
        for genre_name, book_list in books_by_genre.items()
    ]

    return render(request, 'books.html', {'genre_sections': genre_sections, 'search_term': search_term})


def book_detail(request, book_id):
    book = get_object_or_404(Book, book_id=book_id)
    similar_books = Book.objects.select_related('genre_id').filter(
        genre_id=book.genre_id
    ).exclude(book_id=book.book_id).order_by('book_title')[:4]
    return render(request, 'book_detail.html', {'book': book, 'similar_books': similar_books})

def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        school_email = request.POST.get('school_email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = {}

        if not first_name:
            errors['first_name'] = ["First name is required."]
        elif not first_name.isalpha():
            errors['first_name'] = ["First name can only contain letters."]
        elif len(first_name) < 3:
            errors['first_name'] = ["First name must be at least 3 characters."]

        if not last_name:
            errors['last_name'] = ["Last name is required."]
        elif not last_name.isalpha():
            errors['last_name'] = ["Last name can only contain letters."]
        elif len(last_name) < 3:
            errors['last_name'] = ["Last name must be at least 3 characters."]

        if not school_email:
            errors['school_email'] = ["School email is required."]
        elif not school_email.endswith("@ac.school.nz"):
            errors['school_email'] = ["School email must end with '@ac.school.nz'."]

        if not password:
            errors.setdefault('password', []).append("Password is required.")
        if not confirm_password:
            errors.setdefault('confirm_password', []).append("Please confirm your password.")
        if password and confirm_password and password != confirm_password:
            errors.setdefault('password', []).append("Passwords do not match.")

        if Student.objects.filter(school_email__iexact=school_email).exists():
            errors['school_email'] = ["A user with this school email already exists."]

        if errors:
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
            password=make_password(password),
        )
        try:
            student.full_clean()
            student.save()
            messages.success(request, "Registration successful. Please login to continue.")
            return redirect("login")
        except ValidationError as e:
            return render(request, "register.html", {
                "errors": e.message_dict,
                "first_name": first_name,
                "last_name": last_name,
                "school_email": school_email,
            })
    return render(request, "register.html")

def login(request):
    if request.session.get('student_id'):
        return redirect('account')

    if request.method == "POST":
        school_email = request.POST.get("school_email", "").strip()
        password = request.POST.get("password", "")

        errors = {}
        if not school_email:
            errors['school_email'] = ["School email is required."]
        elif not school_email.endswith("@ac.school.nz"):
            errors['school_email'] = ["School email must end with '@ac.school.nz'."]

        if not password:
            errors['password'] = ["Password is required."]

        if errors:
            return render(request, "login.html", {
                "errors": errors,
                "school_email": school_email,
            })

        try:
            student = Student.objects.get(school_email__iexact=school_email)
            if check_password(password, student.password):
                request.session['student_id'] = student.student_id
                request.session['student_name'] = student.first_name
                return redirect('home')
            else:
                return render(request, "login.html", {
                    "error": "Incorrect password. Please try again.",
                    "school_email": school_email,
                })
        except Student.DoesNotExist:
            return render(request, "login.html", {
                "error": "Email is not registered.",
                "school_email": school_email,
            })

    return render(request, "login.html")

def logout_view(request):
    request.session.flush()
    return redirect('home')

def account(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')
    student = Student.objects.filter(student_id=student_id).first()
    if not student:
        request.session.flush()
        return redirect('login')
    return render(request, 'account.html', {'student': student})
