from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from .forms import ContactForm
from .models import Book, Student

# Create your views here.
def home(request):
    all_books = Book.objects.all()
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

def books(request):
    all_books = Book.objects.all()
    return render(request, 'books.html', {'books': all_books})

def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        school_email = request.POST.get('school_email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone_number = request.POST.get('phone_number')

        if password != confirm_password:
            return render(request, "register.html", {
                "errors": {
                    "password": ["Passwords do not match."]
                },
                "first_name": first_name,
                "last_name": last_name,
                "school_email": school_email,
                "phone_number": phone_number,
            })
        student = Student(
            first_name=first_name,
            last_name=last_name,
            school_email=school_email,
            password=make_password(password),
            phone_number=phone_number,
        )
        try:
            # Runs your model clean() validation
            student.full_clean()
            # Saves into Student table
            student.save()
            # Go to login page after success
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
    if request.method == "POST":
        school_email = request.POST.get("school_email")
        password = request.POST.get("password")
        try:
            # Search Student table using email
            student = Student.objects.get(school_email__iexact=school_email.strip())
            # Check password against stored hashed password
            if check_password(password, student.password):
                # Store logged-in student details in session
                request.session['student_id'] = student.student_id
                request.session['student_name'] = student.first_name
                # Login successful
                return redirect("home")
            else:
                # Wrong password
                return render(request, "login.html", {
                    "error": "Incorrect password. Please try again.",
                    "school_email": school_email,
                })
        except Student.DoesNotExist:
            # Email does not exist
            return render(request, "login.html", {
                "error": "Email is not registered.",
                "school_email": school_email,
            })
    return render(request, "login.html")
