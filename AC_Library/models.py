from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
class Student(models.Model): # Each student has a unique ID, first name, last name, and school email.
    student_id = models.AutoField(primary_key = True) # AutoField automatically increments the ID for each new student added to the database.
    first_name = models.CharField(max_length = 15, blank=False) # CharField is used for short text fields. max_length specifies the maximum length of the field, and blank=False means the field cannot be left empty.
    last_name = models.CharField(max_length = 15, blank=False)
    school_email = models.EmailField(max_length = 50, blank=False)

    def clean(self):
        # Checks for any empty fields.
        if not self.first_name or not self.last_name or not self.school_email:
            raise ValidationError("All fields must be provided and cannot be empty.")
        # Validates first and last name.
        if not self.first_name.isalpha():
            raise ValidationError("First name can only contain letters.")
        if len(self.first_name) < 3:
            raise ValidationError("First name must be at least 3 characters.")
        if not self.last_name.isalpha():
            raise ValidationError("Last name can only contain letters.")
        if len(self.last_name) < 3:
            raise ValidationError("Last name must be at least 3 characters.")
        # Validate email by making sure it ends with the correct domain.
        if not self.school_email.endswith("ac.school.nz"):
            raise ValidationError("School email must end with 'ac.school.nz'")
            
    def __str__(self):
        return f"{self.first_name} {self.last_name}" 
    

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    genre_name = models.CharField(max_length=50, blank=False)

    def __str__(self):
        return self.genre_name

class Book(models.Model):
    book_id = models.AutoField(primary_key=True)
    book_genre = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    book_title = models.CharField(max_length=50, blank=False)
    book_author = models.CharField(max_length=50, blank=False)
    book_copies = models.IntegerField(default=1)

    def __str__(self):
        return f"'{self.book_title}' by {self.book_author}"
    
class Issue(models.Model):
    issue_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    issued_book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField()
    overdue_date = models.DateField(null=True, blank=True)

    def clean(self):
        if self.issue_date > self.overdue_date:
            raise ValidationError("Issue date cannot be after the overdue date.")

    def __str__(self):
        return f"{self.student} issued {self.issued_book} on {self.issue_date}"
    
class Return(models.Model):
    return_id = models.AutoField(primary_key=True)
    issue_id = models.ForeignKey(Issue, on_delete=models.CASCADE)
    return_date = models.DateField()

    def clean(self):
        if self.return_date < self.issue_id.issue_date:
            raise ValidationError("Return date cannot be before the issue date.")
        if self.return_date > self.issue_id.overdue_date:
            raise ValidationError("Return date cannot be after the overdue date.")

    def __str__(self):
        return f"{self.student} returned {self.returned_book} on {self.return_date}"
    
