from django.contrib import admin
from django.contrib import messages as django_messages
from django.db.models import F
from datetime import date, timedelta

from .models import Student, Genre, Book, Issue, Return, ContactForm, ReturnRequest

# Register simple models
admin.site.register(Student)
admin.site.register(Genre)
admin.site.register(Book)
admin.site.register(ContactForm)

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('issue_id', 'book_id', 'student_id', 'issue_date', 'overdue_date', 'pickup_ready')
    actions = ['approve_pickup']

    def approve_pickup(self, request, queryset):
        processed = 0
        skipped = 0
        for issue in queryset.filter(pickup_ready=True).select_related('book_id'):
            # Try to reserve a copy atomically
            updated = Book.objects.filter(pk=issue.book_id.pk, book_copies_available__gt=0).update(book_copies_available=F('book_copies_available') - 1)
            if updated == 0:
                skipped += 1
                continue
            issue.pickup_ready = False
            issue.issue_date = date.today()
            issue.overdue_date = date.today() + timedelta(days=14)
            issue.save()
            processed += 1

        if processed:
            self.message_user(request, f"Approved pickup for {processed} issue(s).", level=django_messages.INFO)
        if skipped:
            self.message_user(request, f"{skipped} issue(s) could not be approved — no copies available.", level=django_messages.WARNING)

    approve_pickup.short_description = "Approve pickup for selected issues"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student_id":
            kwargs["queryset"] = Student.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "issue_id":
            kwargs["queryset"] = Issue.objects.filter(return__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'issue_id', 'student_id', 'requested_at', 'processed')
    actions = ['process_requests']

    def process_requests(self, request, queryset):
        processed = 0
        for req in queryset.filter(processed=False):
            # create a Return entry which will run the existing fine and copy-update logic
            Return.objects.create(issue_id=req.issue_id)
            req.processed = True
            req.processed_at = date.today()
            req.save()
            processed += 1
        if processed:
            self.message_user(request, f"Processed {processed} return request(s).", level=django_messages.INFO)

    process_requests.short_description = "Process selected return requests"
