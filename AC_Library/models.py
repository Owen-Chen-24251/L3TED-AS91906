from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.contrib.auth.models import User, Group

# Defining special entities for fields in classes.
def calculate_overdue_date():
    return datetime.today() + timedelta(days=14) # Default overdue date is 14 days from today.

# Create your models here.
class Student(models.Model): # Student model to store student information.
    student_id = models.AutoField(primary_key=True) # Stores the unique ID for each student in the library.
    first_name = models.CharField(max_length = 15, blank=False) # Stores the first name of students, max length of 15.
    last_name = models.CharField(max_length = 15, blank=False) # Stores the last name of students, max length of 15.
    school_email = models.EmailField(max_length = 50, blank=False) # Stores the school email of students, max length of 50.

    def clean(self): # Clean function to validate the data before saving it to the database.
        # Checks for any empty fields.
        if not self.first_name or not self.last_name or not self.school_email: # Checks if any of the fields are empty.
            raise ValidationError({ # Raises error message for empty fields.
                'first_name': "First name is required.", # Error message for first name.
                'last_name': "Last name is required.", # Error message for last name.
                'school_email': "School email is required." # Error message for school email.
            })
        # Validates first and last name.
        if not self.first_name.isalpha() or not self.last_name.isalpha(): # Checks if the first or last name contains only letters (alphabet).
            raise ValidationError({
                'first_name': "First name can only contain letters.", # Error message for first name.
                'last_name': "Last name can only contain letters." # Error message for last name.
            }) 
        if len(self.first_name) < 3 or len(self.last_name) < 3: # Checks if the first or last name is less than 3 characters long.
            raise ValidationError({
                'first_name': "First and last names must be at least 3 characters.", # Error message for first name.
                'last_name': "First and last names must be at least 3 characters." # Error message for last name.
            }) 
        # Validate email by making sure it ends with the correct domain.
        if not self.school_email.endswith("@ac.school.nz"): # Checks if the school email ends with "@ac.school.nz".
            raise ValidationError({
                'school_email': "School email must end with '@ac.school.nz'" # Error message for school email.
            })

    def __str__(self): # Returns the full name of students when data is validated and saved.
        return f"{self.first_name} {self.last_name}" # The printed message is [first name last name].
    
class Category(models.Model): # Category model to store book genres.
    category_id = models.AutoField(primary_key=True) # Stores the unique ID for categories.
    genre_name = models.CharField(max_length=50, blank=False) # Stores the name of the genre, max length of 50.

    def __str__(self): # Returns the genre name when data is validated and saved.
        return self.genre_name # The printed message is the genre name.

class Book(models.Model): # Book model to store book information.
    book_id = models.AutoField(primary_key=True) # Stores the unique ID for each book in the library.
    category_id = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True) # Only uses genres that are available in Category class.
    book_title = models.CharField(max_length=50, blank=False) # Stores the title of the book, max length of 50.
    book_author = models.CharField(max_length=50, blank=False) # Stores the author of the book, max length of 50.
    book_copies_available = models.IntegerField(default=1) # There will always be at least 1 copy of a book, so default is set to 1.

    def __str__(self): # Returns the title and author of the book when data is validated and saved.
        return f"'{self.book_title}' by {self.book_author}" # The printed message is ['book title' by book author].
    
class Issue(models.Model): # Issue model to store information about book issues.
    issue_id = models.AutoField(primary_key=True) # Stores the unique ID for each book issue.
    book_id = models.ForeignKey(Book, on_delete=models.CASCADE) # Only uses books that are available in Book class.
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE) # Only uses students that are available in Student class.
    issue_date = models.DateField(auto_now_add=True) # Automatically sets the date when a book is issued.
    overdue_date = models.DateField(default=calculate_overdue_date) # Stores the date when a book is overdue, which is 14 days after the issue date.

    def clean(self): # Clean function to validate the data before saving it to the database.
        if self.book_id.book_copies_available == 0: # Checks if there are no copies of the book available to issue.
            raise ValidationError("No copies of the book are available to issue.") # Error message.
        if self.book_id.book_copies_available > 0: # If there are copies of the book available to issue, decrease the number of copies by 1.
            self.book_id.book_copies_available -= 1 # Decrease the number of book copies by 1 when a book is issued.
            self.book_id.save() # Save the updated book information to the database.

    def __str__(self): # Returns the student, issued book, and issue date when data is validated and saved.
        # The printed message is [student] issued [issued book] on [issue date].
        return f"{self.student_id} issued {self.book_id.book_title} on {self.issue_date}" 
    
class Return(models.Model): # Return model to store information about book returns.
    return_id = models.AutoField(primary_key=True) # Stores the unique ID for each book return.
    issue_id = models.ForeignKey(Issue, on_delete=models.CASCADE) # Only uses issues that are available in Issue class.
    return_date = models.DateField(default=datetime.today) # Stores todays date when a book is returned.

    def clean(self): # Clean function to validate the data before saving it to the database.
        if self.return_date < self.issue_id.issue_date: # Checks if the return date is before the issue date.
            raise ValidationError("Return date cannot be before the issue date.") # Error message.
        self.issue_id.book_id.book_copies_available += 1 # Increase the number of book copies by 1 when a book is returned.
        self.issue_id.book_id.save() # Save the updated book information to the database.

    def __str__(self): # Returns the student, returned book, and return date when data is validated and saved.
        # The printed message is [student] returned [returned book] on [return date].
        return f"{self.issue_id.student_id} returned {self.issue_id.book_id.book_title} on {self.return_date}"
