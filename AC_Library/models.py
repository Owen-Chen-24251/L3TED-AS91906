# Import necessary modules for the library management system models.
from django.db import models  # Django ORM models base
from django.core.exceptions import ValidationError  # raised for model validation errors
from django.db import transaction  # database transaction helpers
from django.db.models import F  # F expressions for atomic DB updates
from datetime import date, datetime, timedelta  # date utilities used across models
from decimal import Decimal as decimal  # Decimal type for monetary/fine calculations

# Function to calculate overdue date for issued books.
def calculate_overdue_date():  # compute default overdue date (14 days from today)
    return date.today() + timedelta(days=14) # Default overdue date is 14 days from the day a book is issued.

# Library management system models.
# Student model to store student information.
class Student(models.Model):  # model representing a student account
    student_id = models.AutoField(primary_key=True) # Stores the unique ID for each student in the library.
    first_name = models.CharField(max_length = 15, blank=False) # Stores the first name of students, max length of 15.
    last_name = models.CharField(max_length = 15, blank=False) # Stores the last name of students, max length of 15.
    school_email = models.EmailField(max_length = 50, blank=False, unique=True) # Stores the school email of students, max length of 50.
    password = models.CharField(max_length=128, blank=False, default='') # Stores the hashed password for student login.
    fine_amount = models.DecimalField(max_digits=7, decimal_places=2, default=decimal('0.00')) # Stores the fine amount for overdue books for each student.

    def clean(self): # Clean function to validate the data before saving it to the database.
        if not self.first_name or not self.last_name or not self.school_email: # Checks if any of the fields are empty.
            raise ValidationError({ # Raises error message for empty fields.
                'first_name': "First name is required.", # Error message for first name.
                'last_name': "Last name is required.", # Error message for last name.
                'school_email': "School email is required." # Error message for school email.
            })
        # Validates first name.
        if not self.first_name.isalpha(): # Checks if the first name contains only letters (alphabet).
            raise ValidationError({
                'first_name': "First name can only contain letters." # Error message for first name.
            })
        if len(self.first_name) < 3: # Checks if the first name is less than 3 characters long.
            raise ValidationError({
                'first_name': "First name must be at least 3 characters." # Error message for first name.
            })
        # Validates last name.
        if not self.last_name.isalpha(): # Checks if the last name contains only letters (alphabet).
            raise ValidationError({
                'last_name': "Last name can only contain letters." # Error message for last name.
            })
        if len(self.last_name) < 3: # Checks if the last name is less than 3 characters long.
            raise ValidationError({
                'last_name': "Last name must be at least 3 characters." # Error message for last name.
            })
        # Validate email by making sure it ends with the correct domain.
        if not self.school_email.endswith("@ac.school.nz"): # Checks if the school email ends with "@ac.school.nz".
            raise ValidationError({
                'school_email': "School email must end with '@ac.school.nz'" # Error message for school email.
            })

        if Student.objects.filter(school_email__iexact=self.school_email).exclude(pk=self.pk).exists(): 
            # Checks if a student with the same school email already exists in the database, excluding the current instance (for updates).
            raise ValidationError({ # Error message for duplicate school email.
                'school_email': ["A user with this school email already exists."] 
            })

    def __str__(self): # Returns the full name of students when data is validated and saved.
        return f"{self.first_name} {self.last_name}" # Return message.
    
# Genre model to store categories of books in the library.
class Genre(models.Model):  # simple genre/category model for books
    genre_id = models.AutoField(primary_key=True) # Stores the unique ID for genres.
    genre_name = models.CharField(max_length=50, blank=False) # Stores the name of the genre, max length of 50.

    def __str__(self): # Returns the genre name.
        return self.genre_name # Return message.

# Book model to store information about books in the library.
class Book(models.Model):  # model representing a book and its metadata
    book_id = models.AutoField(primary_key=True) # Stores the unique ID for each book in the library.
    genre_id = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True) # Only uses genres that are available in Genre class.
    book_title = models.CharField(max_length=255, blank=False) # Stores the title of the book.
    book_author = models.CharField(max_length=255, blank=False) # Stores the author of the book.
    book_cover = models.ImageField(upload_to='book_covers/', blank=True, null=True) # Stores the cover image of the book.
    book_description = models.TextField(blank=True, null=True) # Stores a synopsis / summary of the book which will be edited by the librarian (admins).
    book_copies_available = models.IntegerField(default=1) # There will always be at least 1 copy of a book, so default is set to 1.

    def __str__(self): # Returns the title and author of the book when data is validated and saved.
        return f"'{self.book_title}' by {self.book_author}" # Return message for book title and author.
    
# Issue model to store information about book issues in the library.
class Issue(models.Model):  # model representing a book issue (loan)
    issue_id = models.AutoField(primary_key=True) # Stores the unique ID for each book issue.
    book_id = models.ForeignKey(Book, on_delete=models.CASCADE, null=True) # Only uses books that are available in Book class.
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE, null=True) # Only uses students that are available in Student class.
    issue_date = models.DateField(auto_now_add=True) # Automatically sets the date when a book is issued.
    overdue_date = models.DateField(default=calculate_overdue_date) # Stores the date when a book is overdue.
    pickup_ready = models.BooleanField(default=False) # Librarian changes this from True to False when the student has picked up the book.

    def clean(self): # Clean function to validate the data before saving it to the database.
        if self.book_id is None: # Checks if a book has been selected for issue.
            raise ValidationError("Please select a book to issue.") # Error message for book selection.
        if self.student_id is None: # Checks if a student has been selected for issue.
            raise ValidationError("Please select a student to issue.") # Error message for student selection.
        # Note: do NOT modify related book counts during validation. Pickup approval
        # is handled by staff in the admin and will decrement the available copy
        # count at the time the student actually picks up the book.

    def __str__(self): # Returns the student, issued book, and issue date when data is validated and saved.
        return f"{self.student_id} issued {self.book_id.book_title} on {self.issue_date}" # Return message for student, issued book, and issue date.

    def save(self, *args, **kwargs):
        # If this is an update where pickup_ready transitions True -> False,
        # this indicates the book was picked up; attempt to decrement copies
        # atomically at that time.
        if self.pk:  # if PK exists this is an update, try to fetch original
            try:
                orig = Issue.objects.get(pk=self.pk)
            except Issue.DoesNotExist:
                orig = None  # original record not found (concurrent delete or new)
        else:
            orig = None

        # Normal save path for new Issues or updates that don't change pickup state
        if not orig or not (orig.pickup_ready and not self.pickup_ready):
            super().save(*args, **kwargs)
            return

        # orig.pickup_ready == True and self.pickup_ready == False => approve pickup
        with transaction.atomic():
            # Attempt to decrement the book copy count in the DB atomically
            updated = Book.objects.filter(pk=self.book_id.pk, book_copies_available__gt=0).update(book_copies_available=F('book_copies_available') - 1)
            if updated == 0:
                raise ValidationError("No copies available to fulfill this pickup.")
            # persist the issue changes (issue_date/overdue_date set by admin)
            super().save(*args, **kwargs)

# Return model to store information about book returns in the library.
class Return(models.Model):  # model representing a returned book
    return_id = models.AutoField(primary_key=True) # Stores the unique ID for each book return.
    issue_id = models.ForeignKey(Issue, on_delete=models.CASCADE, null=True) # Only uses issues that are available in Issue class.
    return_date = models.DateField(default=date.today) # Stores todays date when a book is returned.

    def clean(self): # Clean function to validate the data before saving it to the database.
        if self.issue_id is None: # Checks if an issue has been selected for return.
            raise ValidationError("Please select an issue to return.") # Error message for issue selection.
        if self.return_date < self.issue_id.issue_date: # Checks if the return date is before the issue date.
            raise ValidationError("Return date cannot be before the issue date.") # Error message.
        
    def calculate_days_overdue(self):
        if self.return_date > self.issue_id.overdue_date: # Checks if the return date is after the overdue date.
            return (self.return_date - self.issue_id.overdue_date).days # Calculates the number of days overdue.
        return 0 # If the book is not overdue, returns 0 days overdue.
            
    def save(self, *args, **kwargs): # Save function to calculate the overdue fine and update the book copies when a book is returned.
        if self.return_date > self.issue_id.overdue_date: # Checks if the return date is after the overdue date.
            days_overdue = self.calculate_days_overdue() # Calculate the number of days overdue.
            penalty_fee = decimal("10.00") # Base fine for overdue books.
            overdue_fines = penalty_fee + (days_overdue * decimal("0.50")) # Calculates the fine amount for overdue books. ($10.00 plus $0.50 for each day overdue)
            self.issue_id.student_id.fine_amount += overdue_fines # Add the overdue fine amount to the student's fine amount.
            self.issue_id.student_id.save() # Save the updated student information to the database.
        else:
            pass # If the book is not overdue, do nothing.

        self.issue_id.book_id.book_copies_available += 1 # Increase the number of book copies by 1 when a book is returned.
        self.issue_id.book_id.save() # Save the updated book information to the database.
        super().save(*args, **kwargs) # Saves the return information to the database after calculating fines and updating book copies.

    def __str__(self): # Returns the student, returned book, and return date when data is validated and saved.
        return f"{self.issue_id.student_id} returned {self.issue_id.book_id.book_title} on {self.return_date}" # Return message.
    
class ReturnRequest(models.Model): # Model to store information about return requests in the library.
    request_id = models.AutoField(primary_key=True) # Stores the unique ID for each return request.
    issue_id = models.ForeignKey(Issue, on_delete=models.CASCADE, null=True) # Only uses issues that are available in Issue class.
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE, null=True) # Only uses students that are available in Student class.
    requested_at = models.DateField(default=datetime.today) # Stores the date when a return request is made.
    processed = models.BooleanField(default=False) # Indicates whether the return request has been processed or not.
    processed_at = models.DateField(null=True, blank=True) # Stores the date when a return request is processed. It can be null or blank if the request has not been processed yet.
    admin_notes = models.TextField(blank=True, default='') # Stores any notes or comments made by the admin regarding the return request. It can be blank and has a default empty string.

    def __str__(self): # Returns the issue ID and student ID for the return request when data is validated and saved.
        return f"Return request for {self.issue_id} by {self.student_id}" # Return message for return request.

    def save(self, *args, **kwargs):
        # If this is an update where processed transitions False -> True,
        # create the corresponding Return entry so the system consistently
        # records returns regardless of whether an admin used the action
        # or manually toggled the processed flag in the admin form.
        try:
            orig = None  # placeholder for existing record lookup
            if self.pk:
                orig = ReturnRequest.objects.get(pk=self.pk)  # load original if updating
        except ReturnRequest.DoesNotExist:
            orig = None  # original not found

        # Persist change and create Return when transitioning to processed
        if orig and not orig.processed and self.processed:
            with transaction.atomic():
                # ensure processed_at is set
                if not self.processed_at:
                    self.processed_at = date.today()
                # Create Return if one does not already exist for this issue
                # Use processed_at (if provided) as the return_date so admins
                # can simulate past/future returns when testing in admin.
                if not Return.objects.filter(issue_id=self.issue_id).exists():
                    Return.objects.create(issue_id=self.issue_id, return_date=self.processed_at)
                super().save(*args, **kwargs)
            return

        super().save(*args, **kwargs)

class ContactForm(models.Model): # Model to store information from the contact form submitted by users.
    first_name = models.CharField(max_length = 15) # Stores the first name of the user submitting the contact form, max length of 15.
    last_name = models.CharField(max_length=15) # Stores the last name of the user submitting the contact form, max length of 15.
    email = models.EmailField(max_length=50) # Stores the email address of the user submitting the contact form, max length of 50.
    message = models.TextField(max_length=500, blank=True, default='') # Stores the message submitted by the user, max length of 500.

    def __str__(self): # Returns the first name and last name of the user submitting the contact form when data is validated and saved.
        return f'{self.first_name} - {self.last_name}' # Return message for contact form submission.