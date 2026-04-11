from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
import pycountry

from .forms import (
    ApplicantBasicInfoForm,
    ApplicantDocumentsForm,
    EducationQualificationForm,
    EmploymentHistoryForm,
)
from .models import (
    ApplicantDocument,
    ApplicantProfile,
    EducationQualification,
    EmploymentHistory,
)


def get_applicant_profile(user):
    profile, _ = ApplicantProfile.objects.get_or_create(user=user)
    return profile


@login_required
def dashboard(request):
    profile = get_applicant_profile(request.user)
    qualifications_count = profile.qualifications.count()
    employments_count = profile.employments.count()
    documents_count = profile.documents.count()

    completed_steps = 0
    if profile.has_step1():
        completed_steps += 1
    if profile.has_step2():
        completed_steps += 1
    if profile.has_step3():
        completed_steps += 1
    if profile.has_step4():
        completed_steps += 1

    progress_percent = int((completed_steps / 4) * 100)

    return render(request, 'applicant/dashboard.html', {
        'profile': profile,
        'profile_complete': profile.profile_is_complete(),
        'qualifications_count': qualifications_count,
        'employments_count': employments_count,
        'documents_count': documents_count,
        'completed_steps': completed_steps,
        'progress_percent': progress_percent,
    })


@login_required
def profile_step1(request):
    profile = get_applicant_profile(request.user)

    if request.method == 'POST':
        form = ApplicantBasicInfoForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Basic information saved successfully.')
            return redirect('applicant:profile_step2')
    else:
        form = ApplicantBasicInfoForm(instance=profile, user=request.user)

    # Sort country choices alphabetically for better UX
    form.fields['country'].choices = sorted(form.fields['country'].choices, key=lambda x: x[1])

    return render(request, 'applicant/profile_step1.html', {
        'form': form,
        'profile': profile,
        'current_step': 1,
    })


@login_required
def profile_step2(request):
    profile = get_applicant_profile(request.user)
    resume = profile.documents.filter(document_type=ApplicantDocument.DOCUMENT_RESUME).first()
    grade8 = profile.documents.filter(document_type=ApplicantDocument.DOCUMENT_GRADE_8).first()

    if request.method == 'POST':
        form = ApplicantDocumentsForm(request.POST, request.FILES)
        if form.is_valid():
            resume_file = form.cleaned_data.get('resume')
            grade8_file = form.cleaned_data.get('grade_8_certificate')

            if resume_file:
                ApplicantDocument.objects.update_or_create(
                    applicant=profile,
                    document_type=ApplicantDocument.DOCUMENT_RESUME,
                    defaults={'file': resume_file}
                )

            if grade8_file:
                ApplicantDocument.objects.update_or_create(
                    applicant=profile,
                    document_type=ApplicantDocument.DOCUMENT_GRADE_8,
                    defaults={'file': grade8_file}
                )

            messages.success(request, 'Documents saved successfully.')
            return redirect('applicant:profile_step3')
    else:
        form = ApplicantDocumentsForm()

    return render(request, 'applicant/profile_step2.html', {
        'form': form,
        'profile': profile,
        'resume': resume,
        'grade8': grade8,
        'current_step': 2,
    })


@login_required
def profile_step3(request):
    profile = get_applicant_profile(request.user)
    qualifications = profile.qualifications.all()

    if request.method == 'POST':
        form = EducationQualificationForm(request.POST, request.FILES)
        if form.is_valid():
            qualification = form.save(commit=False)
            qualification.profile = profile
            qualification.save()
            messages.success(request, 'Qualification added successfully.')
            return redirect('applicant:profile_step3')
    else:
        form = EducationQualificationForm()

    return render(request, 'applicant/profile_step3.html', {
        'form': form,
        'profile': profile,
        'qualifications': qualifications,
        'current_step': 3,
    })


@login_required
def profile_step4(request):
    profile = get_applicant_profile(request.user)
    employments = profile.employments.all()

    if request.method == 'POST':
        form = EmploymentHistoryForm(request.POST, request.FILES)
        if form.is_valid():
            employment = form.save(commit=False)
            employment.profile = profile
            employment.save()
            messages.success(request, 'Employment history added successfully.')
            return redirect('applicant:profile_step4')
    else:
        form = EmploymentHistoryForm()

    return render(request, 'applicant/profile_step4.html', {
        'form': form,
        'profile': profile,
        'employments': employments,
        'current_step': 4,
    })


@login_required
def apply_jobs(request):
    profile = get_applicant_profile(request.user)
    if not profile.profile_is_complete():
        messages.warning(request, 'Please complete your applicant profile before applying for jobs.')
        return redirect('applicant:profile_step1')

    return render(request, 'applicant/apply_jobs.html', {
        'profile': profile,
    })


@login_required
def applications(request):
    profile = get_applicant_profile(request.user)
    if not profile.profile_is_complete():
        messages.warning(request, 'Please complete your profile before reviewing applications.')
        return redirect('applicant:profile_step1')

    return render(request, 'applicant/applications.html', {
        'profile': profile,
    })


@login_required
def edit_profile(request):
    profile = get_applicant_profile(request.user)
    return render(request, 'applicant/edit_profile.html', {
        'profile': profile,
    })


class ApplicantPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'applicant/change_password.html'
    success_url = reverse_lazy('applicant:dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'Your password was changed successfully.')
        return super().form_valid(form)
