from django.contrib import admin
from .models import Student, Category, Book, Issue, Return

# Register your models here.
admin.site.register(Student)
admin.site.register(Category)
admin.site.register(Book)
admin.site.register(Issue)
admin.site.register(Return)