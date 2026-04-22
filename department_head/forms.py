from django import forms
from django.forms import inlineformset_factory
from .models import EmployeeRequest, EmployeeRequestItem


class EmployeeRequestForm(forms.ModelForm):
    class Meta:
        model = EmployeeRequest
        fields = ('subject', 'request_narrative')

        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),

            'request_narrative': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'id': 'id_request_narrative'
            }),
        }


class EmployeeRequestItemForm(forms.ModelForm):
    class Meta:
        model = EmployeeRequestItem
        exclude = ('request',)

        widgets = {
            'academic_qualification': forms.Select(attrs={'class': 'form-control'}),
            'academic_rank': forms.Select(attrs={'class': 'form-control'}),

            # manual input field
            'study_department': forms.TextInput(attrs={'class': 'form-control'}),

            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),

            'cgpa_requirement': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),

            'number_of_employees': forms.NumberInput(attrs={'class': 'form-control'}),

            'no': forms.NumberInput(attrs={'class': 'form-control'}),
        }


EmployeeRequestItemFormset = inlineformset_factory(
    EmployeeRequest,
    EmployeeRequestItem,
    form=EmployeeRequestItemForm,
    extra=0,
    can_delete=True,
)


EmployeeRequestItemFormsetCreate = inlineformset_factory(
    EmployeeRequest,
    EmployeeRequestItem,
    form=EmployeeRequestItemForm,
    extra=1,
    can_delete=True,
)