from django import forms
from .models import Contact

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['first name', 'last name', 'email', 'message'] # The fields you want in your form
