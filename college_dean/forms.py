from django import forms


class ApproveForm(forms.Form):
    confirm = forms.BooleanField(required=True, label='Confirm approval')


class RejectForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True, label='Reason for rejection')


class ForwardForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label='Note to VP')
