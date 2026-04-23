from django.contrib.auth.models import User, Group
from django.contrib import admin
from .models import Student, Category, Book, Issue, Return

# Register your models here.
admin.site.register(Student)
admin.site.register(Category)
admin.site.register(Book)

# Saving the models.
@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
            if db_field.name == "student_id": # Checks if the foreign key field is 'student_id'.
                kwargs["queryset"] = Student.objects.all() # Filter the queryset to only include students who are not currently assigned to an issue.
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
            if db_field.name == "issue_id": # Checks if the foreign key field is 'issue_id'.
                kwargs["queryset"] = Issue.objects.filter(return__isnull=True) # Filter the queryset to only include issues that have not been returned yet.
            return super().formfield_for_foreignkey(db_field, request, **kwargs)