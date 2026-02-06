from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from captcha.fields import CaptchaField  # simple captcha


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={'placeholder': 'Your Name'})
    )
    father_name = forms.CharField(
        max_length=30,
        required=True,
        label="Father Name",
        widget=forms.TextInput(attrs={'placeholder': 'Your Father Name'})
    )
    grand_father_name = forms.CharField(
        max_length=30,
        required=True,
        label="Grand Father Name",
        widget=forms.TextInput(attrs={'placeholder': 'Your Grand Father Name'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={'placeholder': 'Your Phone Number'})
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'placeholder': 'Your Email Address'})
    )
    captcha = CaptchaField(label="CAPTCHA")

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'father_name',
            'grand_father_name',
            'email',
            'phone_number',
            'password1',
            'password2',
            'captcha',
]

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already in use.")
        return email
