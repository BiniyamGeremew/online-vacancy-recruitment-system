from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib.auth import login
from django.conf import settings

from .registration_form import RegisterForm


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.groups.filter(name='applicant').exists():
            return reverse_lazy('applicant:dashboard')
        if user.groups.filter(name='hr_officer').exists():
            return reverse_lazy('hr_officer:dashboard')
        return reverse_lazy('accounts:login')  


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


def send_activation_email(request, user):
    current_site = get_current_site(request)
    subject = 'Activate your account'
    message = render_to_string('accounts/activation_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def register_view(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        send_activation_email(request, user)
        return redirect('registration_complete')

    return render(request, 'accounts/register.html', {'form': form})


def activate_account(request, uid, token):
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = get_object_or_404(User, pk=uid)
    except (TypeError, ValueError, OverflowError):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('home')

    return render(request, 'accounts/activation_invalid.html')
