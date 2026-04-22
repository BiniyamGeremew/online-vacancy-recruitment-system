from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.utils import timezone

from hr_officer.models import Vacancy, VacancyPosition, JobApplication
from hr_officer.constants import VacancyStatus

from .models import (
    ApplicantProfile,
    EducationQualification,
    EmploymentHistory,
    ApplicantDocument,
)
from .forms import (
    ApplicantBasicInfoForm,
    ApplicantDocumentsForm,
    EducationQualificationForm,
    EmploymentHistoryForm,
)

def get_applicant_profile(user):
    profile, _ = ApplicantProfile.objects.get_or_create(user=user)
    return profile


@login_required
def vacancy_board_list(request):
    vacancies = Vacancy.objects.filter(
        status=VacancyStatus.PUBLISHED
    ).order_by('-announcement_date')

    return render(request, 'applicant/vacancy_board_list.html', {
        'vacancies': vacancies
    })


@login_required
def vacancy_board_detail(request, id):
    vacancy = get_object_or_404(
        Vacancy,
        id=id,
        status=VacancyStatus.PUBLISHED
    )

    positions = vacancy.positions.all()

    applied_positions = JobApplication.objects.filter(
        applicant=request.user,
        vacancy_position__vacancy=vacancy
    ).values_list('vacancy_position_id', flat=True)

    today = timezone.now().date()

    return render(request, 'applicant/vacancy_board_detail.html', {
        'vacancy': vacancy,
        'positions': positions,
        'applied_positions': applied_positions,
        'today': today,
    })


@login_required
def apply(request, position_id):
    user = request.user
    profile = get_applicant_profile(user)

    position = get_object_or_404(
        VacancyPosition,
        id=position_id,
        vacancy__status=VacancyStatus.PUBLISHED
    )

    vacancy = position.vacancy

    if vacancy.deadline and vacancy.deadline < timezone.now().date():
        messages.warning(request, 'The application deadline has passed.')
        return redirect('applicant:vacancy_board_detail', id=vacancy.id)

    # duplicate check
    if JobApplication.objects.filter(
        applicant=user,
        vacancy_position=position
    ).exists():
        messages.warning(request, 'You already applied for this position.')
        return redirect('applicant:vacancy_board_detail', id=vacancy.id)

    # profile check
    if not profile.profile_is_complete():
        messages.warning(request, 'Complete your profile first.')
        return redirect('applicant:edit_profile')

    education = EducationQualification.objects.filter(profile=profile)
    employment = EmploymentHistory.objects.filter(profile=profile)
    documents = ApplicantDocument.objects.filter(applicant=profile)

    if request.method == 'POST':
        JobApplication.objects.create(
            applicant=user,
            applicant_profile=profile,
            vacancy_position=position,
            status='submitted'
        )

        messages.success(request, 'Application submitted successfully!')
        return redirect('applicant:vacancy_board_list')

    return render(request, 'applicant/application_review.html', {
        'profile': profile,
        'user': user,
        'education': education,
        'employment': employment,
        'documents': documents,
        'position': position
    })

@login_required
def dashboard(request):
    profile = get_applicant_profile(request.user)

    return render(request, 'applicant/dashboard.html', {
        'profile': profile,
        'profile_complete': profile.profile_is_complete(),
        'qualifications_count': profile.qualifications.count(),
        'employments_count': profile.employments.count(),
        'documents_count': profile.documents.count(),
    })


# ===================== PROFILE STEPS =====================
@login_required
def profile_step1(request):
    profile = get_applicant_profile(request.user)

    if request.method == 'POST':
        form = ApplicantBasicInfoForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('applicant:profile_step2')
    else:
        form = ApplicantBasicInfoForm(instance=profile, user=request.user)

    return render(request, 'applicant/profile_step1.html', {
        'form': form,
        'profile': profile,
        'current_step': 1,
    })


@login_required
def profile_step2(request):
    profile = get_applicant_profile(request.user)

    form = ApplicantDocumentsForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data.get('resume'):
            ApplicantDocument.objects.update_or_create(
                applicant=profile,
                document_type=ApplicantDocument.DOCUMENT_RESUME,
                defaults={'file': form.cleaned_data['resume']}
            )

        if form.cleaned_data.get('grade_8_certificate'):
            ApplicantDocument.objects.update_or_create(
                applicant=profile,
                document_type=ApplicantDocument.DOCUMENT_GRADE_8,
                defaults={'file': form.cleaned_data['grade_8_certificate']}
            )

        return redirect('applicant:profile_step3')

    return render(request, 'applicant/profile_step2.html', {
        'form': form,
        'profile': profile,
        'current_step': 2,
    })


@login_required
def profile_step3(request):
    profile = get_applicant_profile(request.user)

    if request.method == 'POST':
        form = EducationQualificationForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.profile = profile
            obj.save()
            return redirect('applicant:profile_step3')
    else:
        form = EducationQualificationForm()

    return render(request, 'applicant/profile_step3.html', {
        'form': form,
        'profile': profile,
        'qualifications': profile.qualifications.all(),
        'current_step': 3,
    })


@login_required
def profile_step4(request):
    profile = get_applicant_profile(request.user)

    if request.method == 'POST':
        form = EmploymentHistoryForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.profile = profile
            obj.save()
            return redirect('applicant:profile_step4')
    else:
        form = EmploymentHistoryForm()

    return render(request, 'applicant/profile_step4.html', {
        'form': form,
        'profile': profile,
        'employments': profile.employments.all(),
        'current_step': 4,
    })


@login_required
def vacancy_board_list(request):
    vacancies = Vacancy.objects.filter(
        status=VacancyStatus.PUBLISHED
    ).order_by('-announcement_date')

    return render(request, 'applicant/vacancy_board_list.html', {
        'vacancies': vacancies
    })


@login_required
def applications(request):
    profile = get_applicant_profile(request.user)

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
        messages.success(self.request, 'Password changed successfully.')
        return super().form_valid(form)