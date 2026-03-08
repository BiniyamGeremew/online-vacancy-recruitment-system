from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import Group

from .registration_form import RegisterForm
from .forms import EmailAuthenticationForm
from .models import UserProfile


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = EmailAuthenticationForm

    def get_success_url(self):
        user = self.request.user
        if user.groups.filter(name='applicant').exists():
            return reverse_lazy('applicant:dashboard')
        if user.groups.filter(name='hr_officer').exists():
            return reverse_lazy('hr_officer:dashboard')
        if user.groups.filter(name='department_head').exists():
            return reverse_lazy('department_head:dashboard')
        if user.groups.filter(name='college_dean').exists():
            return reverse_lazy('college_dean:dashboard')
        if user.groups.filter(name='academic_vp').exists():
            return reverse_lazy('academic_vp:dashboard')
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
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Create user (use email as username)
            user = form.save(commit=False)
            email = form.cleaned_data['email'].lower()
            user.email = email
            user.username = email
            user.is_active = False
            user.save()

            # Create profile
            UserProfile.objects.create(
                user=user,
                father_name=form.cleaned_data['father_name'],
                grand_father_name=form.cleaned_data['grand_father_name'],
                phone_number=form.cleaned_data.get('phone_number')
            )

            # Assign to applicant group
            group, _ = Group.objects.get_or_create(name='applicant')
            user.groups.add(group)

            # Send activation email
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

            messages.success(
                request,
                'Registration successful! Please check your email to activate your account.'
            )
            return redirect('accounts:register')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def activate_account(request, uid, token):
    user = None
    try:
        uid_decoded = force_str(urlsafe_base64_decode(uid))
        uid_int = int(uid_decoded)
        user = User.objects.filter(pk=uid_int).first()
    except (TypeError, ValueError, OverflowError):
        user = None

    # Check user exists and token is valid
    if user and default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save()

        login(request, user)
        messages.success(request, "Your account has been activated!")
        return redirect('applicant:dashboard')

    return render(request, 'accounts/activation_invalid.html', {
        'reason': 'The activation link is invalid or has expired.'
    })