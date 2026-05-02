from django import forms
from django.contrib.auth.models import User

from .models import VPProfile


class ApproveRequestForm(forms.Form):
    confirm = forms.BooleanField(required=True, label='Confirm approval')


class RejectRequestForm(forms.Form):
    rejection_reason = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=True, label='Reason for rejection')


class ForwardRequestForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False, label='Note to HR')


class AcademicVPUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class AcademicVPProfileForm(forms.ModelForm):
    class Meta:
        model = VPProfile
        fields = ('phone_number', 'office_location', 'bio')
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'office_location': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
