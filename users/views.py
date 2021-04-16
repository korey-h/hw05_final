from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ContactForm, CreationForm
from .models import Contact


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy("signup")
    template_name = "signup.html"


def user_contact(request):

    contact = Contact.objects.get(pk=3)
    form = ContactForm(instance=contact)

    return render(request, 'contact.html', {'form': form})


def test_index(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            new_contact = form.save()
            print('new contact ', new_contact.id)
    else:
        form = ContactForm()

    return render(request, 'user_index.html', {'form': form})
