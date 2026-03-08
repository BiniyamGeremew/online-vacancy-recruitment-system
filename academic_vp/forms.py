from django import forms


class ApproveRequestForm(forms.Form):
    confirm = forms.BooleanField(required=True, label='Confirm approval')


class RejectRequestForm(forms.Form):
    rejection_reason = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=True, label='Reason for rejection')


class ForwardRequestForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False, label='Note to HR')
