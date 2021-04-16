from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Contact

User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email")


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ('name', 'email', 'subject', 'body')

    def clean_email(self):
        data = self.cleaned_data['email']
        amount = Contact.objects.filter(email=data).count()
        if amount > 0:
            raise forms.ValidationError("Такой емэйл уже существует. \
                                         Введите новый")
        return data
