from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import Exam


class ExamCreateForm(forms.ModelForm):
    question_count = forms.IntegerField(
        min_value=1,
        max_value=40,
        initial=10,
        required=True,
        help_text='Total number of questions to generate with AI.',
    )

    mcq_count = forms.IntegerField(
        min_value=0,
        max_value=40,
        initial=10,
        required=True,
        help_text='Number of MCQ questions in the generated exam.',
    )

    short_answer_count = forms.IntegerField(
        min_value=0,
        max_value=40,
        initial=0,
        required=True,
        help_text='Number of short-answer questions in the generated exam.',
    )

    difficulty_level = forms.ChoiceField(
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        initial='medium',
        required=False,
        help_text='AI difficulty level when generating questions.',
    )

    class Meta:
        model = Exam
        fields = [
            'title',
            'start_time',
            'duration_minutes',
            'total_marks',
            'pass_mark',
            'is_published',
        ]

        widgets = {
            # ✅ FIXED: no auto-fill, no required forcing
            'start_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'placeholder': 'Select exam start time'
                },
                format='%Y-%m-%dT%H:%M'
            ),

            'duration_minutes': forms.NumberInput(attrs={'min': 5}),
            'total_marks': forms.NumberInput(attrs={'min': 1}),
            'pass_mark': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Ensure start_time is NOT required (important fix)
        self.fields['start_time'].required = False

    def clean_start_time(self):
        """
        Treat the datetime-local input as UTC to avoid timezone confusion.
        """
        start_time = self.cleaned_data.get('start_time')
        if start_time and timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time, timezone.utc)
        return start_time

    def clean_pass_mark(self):
        total_marks = self.cleaned_data.get('total_marks')
        if total_marks is None:
            return 0
        return int(Decimal(total_marks) * Decimal('0.5'))