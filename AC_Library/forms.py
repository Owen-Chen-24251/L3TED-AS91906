from django import forms  # Django forms framework
from .models import ContactForm as ContactFormModel  # Contact model to persist messages


class ContactForm(forms.ModelForm):
    """Simple ModelForm for the ContactForm model used on the About page.

    Keeps only the visible fields required for users to submit a contact message.
    """
    class Meta:
        model = ContactFormModel
        fields = ['first_name', 'last_name', 'email', 'message']  # fields exposed in the form
