from django import forms
from django.forms import inlineformset_factory
from .models import EmployeeRequest, EmployeeRequestItem


class EmployeeRequestForm(forms.ModelForm):
    class Meta:
        model = EmployeeRequest
        fields = ('subject', 'description', 'closing_note')
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'closing_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EmployeeRequestItemForm(forms.ModelForm):
    class Meta:
        model = EmployeeRequestItem
        exclude = ('request',)
        widgets = {
            'academic_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_rank': forms.TextInput(attrs={'class': 'form-control'}),
            'area_of_specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'cgpa_requirement': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'number_of_employees': forms.NumberInput(attrs={'class': 'form-control'}),
            'no': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# Formset used on the update page: show only existing items (no extra blank form)
EmployeeRequestItemFormset = inlineformset_factory(
    EmployeeRequest,
    EmployeeRequestItem,
    form=EmployeeRequestItemForm,
    extra=0,
    can_delete=True,
)

# Formset used on the create page: allow adding one blank form by default
EmployeeRequestItemFormsetCreate = inlineformset_factory(
    EmployeeRequest,
    EmployeeRequestItem,
    form=EmployeeRequestItemForm,
    extra=1,
    can_delete=True,
)
