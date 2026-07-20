from django import forms
from .models import ContactForm as ContactFormModel

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactFormModel
        fields = ['first_name', 'last_name', 'email', 'message'] # The fields you want in your form
