from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.models import User

from .models import Vacancy, VacancyPosition, JobApplication, HRProfile


class VacancyForm(forms.ModelForm):

    class Meta:
        model = Vacancy
        fields = [
            "vacancy_type",
            "experience_requirement",
            "required_skills",
            "salary_info",
            "deadline",
            "application_instructions",
            "announcement_text",
        ]

        widgets = {

            "vacancy_type": forms.Select(attrs={
                "class": "form-control"
            }),

            "experience_requirement": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "required_skills": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2
            }),

            "salary_info": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "deadline": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            "application_instructions": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

            "announcement_text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 10
            }),
        }


class VacancyPositionForm(forms.ModelForm):

    class Meta:
        model = VacancyPosition
        fields = [
            "department",
            "academic_rank",
            "field_of_education",
            "minimum_cgpa",
            "positions",
        ]

        widgets = {
            "department": forms.Select(attrs={
                "class": "form-control"
            }),

            "academic_rank": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "field_of_education": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "minimum_cgpa": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }),

            "positions": forms.NumberInput(attrs={
                "class": "form-control"
            }),
        }


# ================= FORMSET =================

VacancyPositionFormSet = inlineformset_factory(
    Vacancy,
    VacancyPosition,
    form=VacancyPositionForm,
    extra=1,
    can_delete=True
)


class JobApplicationForm(forms.ModelForm):

    class Meta:
        model = JobApplication
        fields = []  # auto-filled from system


class HROfficerUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class HRProfileForm(forms.ModelForm):
    class Meta:
        model = HRProfile
        fields = ('phone_number', 'office_location', 'bio')
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'office_location': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }