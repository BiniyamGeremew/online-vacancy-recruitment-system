from django import forms
from .models import Exam, Question


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


class ManualQuestionForm(forms.Form):
    question_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True)
    question_type = forms.ChoiceField(
        choices=Question.QUESTION_TYPE_CHOICES,
        initial=Question.TYPE_MCQ,
        required=True,
    )
    marks = forms.IntegerField(min_value=1, initial=1, required=True)
    choice_1 = forms.CharField(required=False)
    choice_2 = forms.CharField(required=False)
    choice_3 = forms.CharField(required=False)
    choice_4 = forms.CharField(required=False)
    correct_choice = forms.ChoiceField(
        choices=[('1', 'Choice 1'), ('2', 'Choice 2'), ('3', 'Choice 3'), ('4', 'Choice 4')],
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')

        if question_type == Question.TYPE_MCQ:
            choices = [
                cleaned_data.get('choice_1'),
                cleaned_data.get('choice_2'),
                cleaned_data.get('choice_3'),
                cleaned_data.get('choice_4'),
            ]
            if not all(choices):
                raise forms.ValidationError('All four MCQ choices are required.')

            correct_choice = cleaned_data.get('correct_choice')
            if not correct_choice or not cleaned_data.get(f'choice_{correct_choice}'):
                raise forms.ValidationError('A valid correct choice is required for MCQ questions.')

        return cleaned_data


class QuestionUploadForm(forms.Form):
    questions_file = forms.FileField(required=True)

    def clean_questions_file(self):
        file = self.cleaned_data['questions_file']
        if not file.name.endswith('.json'):
            raise forms.ValidationError('Upload a JSON file with questions.')
        return file
