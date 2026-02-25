from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models import Q


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label=_("Email"), widget=forms.EmailInput)

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            # find user by email
            user_qs = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email))
            if user_qs.exists():
                username = user_qs.first().get_username()
                self.user_cache = authenticate(self.request, username=username, password=password)
            else:
                self.user_cache = None

            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': getattr(self.username_field, 'verbose_name', 'username')},
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
