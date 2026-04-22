from django import forms
from django.forms import inlineformset_factory

from .models import Vacancy, VacancyPosition, JobApplication


class VacancyForm(forms.ModelForm):

    class Meta:
        model = Vacancy
        fields = [
            "vacancy_type",
            "experience_requirement",
            "required_skills",
            "salary_info",
            "announcement_date",
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

            "announcement_date": forms.DateInput(attrs={
                "type": "date",
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