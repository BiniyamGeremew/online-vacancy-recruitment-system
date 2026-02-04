from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from captcha.fields import CaptchaField  # simple captcha


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    father_name = forms.CharField(max_length=30, required=True, label="Father Name")
    grand_father_name = forms.CharField(max_length=30, required=True, label="Grand Father Name")
    email = forms.EmailField(required=True, label="Email")
    captcha = CaptchaField(label="Verification Code")

    class Meta:
        model = User
        fields = [
            'first_name',
            'father_name',
            'grand_father_name',
            'email',
            'username',
            'password1',
            'password2',
            'captcha',
        ]
