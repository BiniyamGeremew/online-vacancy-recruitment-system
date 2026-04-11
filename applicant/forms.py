from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import pycountry

from .models import ApplicantProfile, EducationQualification, EmploymentHistory


class ApplicantFormMixin:
    def _apply_form_control(self):
        for field_name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} form-control'.strip()
            if field.required:
                field.widget.attrs['placeholder'] = field.label


# Generate ISO-standard country choices
COUNTRY_CHOICES = [(c.alpha_2, c.name) for c in pycountry.countries]

TITLE_CHOICES = [
    ('Mr', 'Mr'),
    ('Ms', 'Ms'),
    ('Mrs', 'Mrs'),
    ('Dr', 'Dr'),
    ('Prof', 'Prof'),
    ('Eng', 'Eng'),
]

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
]

REGION_CHOICES = [
    ('Addis Ababa', 'Addis Ababa'),
    ('Afar', 'Afar'),
    ('Amhara', 'Amhara'),
    ('Benishangul-Gumuz', 'Benishangul-Gumuz'),
    ('Dire Dawa', 'Dire Dawa'),
    ('Gambela', 'Gambela'),
    ('Harari', 'Harari'),
    ('Oromia', 'Oromia'),
    ('Sidama', 'Sidama'),
    ('Somali', 'Somali'),
    ('South West Ethiopia', 'South West Ethiopia'),
    ('SNNP', 'Southern Nations Nationalities and Peoples'),
    ('Tigray', 'Tigray'),
]


class ApplicantBasicInfoForm(ApplicantFormMixin, forms.ModelForm):
    email = forms.EmailField()
    first_name = forms.CharField(label="Name")          
    father_name = forms.CharField(label="Father Name")    
    last_name = forms.CharField(label="Grandfather Name")

    title = forms.ChoiceField(choices=[('', 'Select Title')] + TITLE_CHOICES)
    gender = forms.ChoiceField(choices=[('', 'Select Gender')] + GENDER_CHOICES)
    country = forms.ChoiceField(choices=[('', 'Select Country')] + COUNTRY_CHOICES)
    region = forms.ChoiceField(choices=[('', 'Select Region')] + REGION_CHOICES)

    class Meta:
        model = ApplicantProfile
        fields = [
            'title',
            'first_name',   
            'father_name',
            'last_name',    
            'mobile_number',
            'birth_date',
            'marital_status',
            'gender',
            'country',
            'region',
            'zone',
            'wereda',
            'kebele',
            'house_number',
            'postal_code',
            'email',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'marital_status': forms.Select(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_form_control()

        if user is not None:
            self.fields['email'].initial = user.email
            self.fields['first_name'].initial = user.first_name
            self.fields['father_name'].initial = getattr(self.instance, 'father_name', '')
            self.fields['last_name'].initial = user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.email = self.cleaned_data.get('email', user.email)
        user.first_name = self.cleaned_data.get('first_name', user.first_name)
        user.last_name = self.cleaned_data.get('last_name', user.last_name)
        if commit:
            user.save()
            profile.save()
        return profile


class ApplicantDocumentsForm(ApplicantFormMixin, forms.Form):
    resume = forms.FileField(required=False)
    grade_8_certificate = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_form_control()
        self.fields['resume'].widget.attrs['class'] = 'form-control-file'
        self.fields['grade_8_certificate'].widget.attrs['class'] = 'form-control-file'


class EducationQualificationForm(ApplicantFormMixin, forms.ModelForm):
    qualification_type = forms.ChoiceField(choices=[('', 'Select Qualification Type')], required=True)

    class Meta:
        model = EducationQualification
        fields = [
            'institution_name',
            'qualification_category',
            'qualification_type',
            'department',
            'grade',
            'start_date',
            'end_date',
            'diploma_certificate',
            'transcript',
            'cost_sharing_document',
        ]
        widgets = {
            'grade': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '4'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'diploma_certificate': forms.ClearableFileInput(),
            'transcript': forms.ClearableFileInput(),
            'cost_sharing_document': forms.ClearableFileInput(),
        }

    QUALIFICATION_TYPE_MAP = {
    "bachelor": [
        ("LLB", "LLB"),
        ("B.Ed", "B.Ed"),
        ("B.A", "B.A"),
        ("B.Sc", "B.Sc"),
        ("Medical Doctor", "Medical Doctor")
    ],
    "post_graduate": [
        ("MAL", "Master of Art in Leadership (MAL)"),
        ("Master of Commerce", "Master of Commerce"),
        ("M.A", "M.A"),
        ("EMBA", "EMBA"),
        ("MBA", "MBA"),
        ("Post Graduate Diploma", "Post Graduate Diploma"),
        ("M.Sc", "M.Sc"),
        ("LLM", "LLM")
    ],
    "doctorate": [
        ("PhD", "PhD"),
        ("Medical Doctor", "Medical Doctor")
    ]
}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_form_control()

        # File inputs styling
        self.fields['diploma_certificate'].widget.attrs['class'] = 'form-control-file'
        self.fields['transcript'].widget.attrs['class'] = 'form-control-file'
        self.fields['cost_sharing_document'].widget.attrs['class'] = 'form-control-file'

        # Dynamically populate qualification_type based on POST
        category = None
        if self.is_bound:
            category = self.data.get('qualification_category')
        elif self.instance and self.instance.qualification_category:
            category = self.instance.qualification_category

        if category and category in self.QUALIFICATION_TYPE_MAP:
            self.fields['qualification_type'].choices = [('', 'Select Qualification Type')] + self.QUALIFICATION_TYPE_MAP[category]
        else:
            self.fields['qualification_type'].choices = [('', 'Select Qualification Type')]

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end and end < start:
            raise forms.ValidationError("End date cannot be before start date.")

        return cleaned_data

class EmploymentHistoryForm(ApplicantFormMixin, forms.ModelForm):
    class Meta:
        model = EmploymentHistory
        fields = [
            'job_category',
            'employer',
            'job_title',
            'start_date',
            'end_date',
            'experience_letter',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'experience_letter': forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_form_control()
        self.fields['experience_letter'].widget.attrs['class'] = 'form-control-file'

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise ValidationError('End date cannot be earlier than start date.')

        return cleaned_data