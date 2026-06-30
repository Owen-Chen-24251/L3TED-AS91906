from django.shortcuts import render, redirect
from .models import Book, ContactForm

# Create your views here.
def home(request):
    return render(request, 'home.html')

def aboutus(request):
    if request.method == 'POST':
        form = ContactForm(request.POST) # Pass the submitted data to the form
        if form.is_valid():               # Automatically validates field types and constraints
            form.save()                   # Saves the data directly to your database table
            return redirect('success_url') # Redirect to a success page
    else:
        form = ContactForm()             # Provide a blank form for GET requests
    return render(request, 'aboutus.html', {'form': form})

def books(request):
    all_books = Book.objects.all()
    return render(request, 'books.html', {'books': all_books})
