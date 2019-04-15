from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    name = forms.CharField(max_length=50, required=True, help_text='Your name')

    class Meta:
        model = User
        fields = ('username', 'name', 'password1', 'password2')

