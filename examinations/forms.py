from django import forms
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
            'duration_minutes',
            'total_marks',
            'pass_mark',
            'is_published',
        ]
        widgets = {
            'duration_minutes': forms.NumberInput(attrs={'min': 5}),
            'total_marks': forms.NumberInput(attrs={'min': 1}),
            'pass_mark': forms.NumberInput(attrs={'min': 1}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total_marks = cleaned_data.get('total_marks')
        pass_mark = cleaned_data.get('pass_mark')

        if total_marks is not None and pass_mark is not None and pass_mark > total_marks:
            self.add_error('pass_mark', 'Pass mark should not be greater than total marks.')

        question_count = cleaned_data.get('question_count')
        mcq_count = cleaned_data.get('mcq_count')
        short_answer_count = cleaned_data.get('short_answer_count')

        if question_count is not None and mcq_count is not None and short_answer_count is not None:
            if mcq_count + short_answer_count != question_count:
                raise forms.ValidationError('MCQ count and short-answer count must add up to the total question count.')

        return cleaned_data


