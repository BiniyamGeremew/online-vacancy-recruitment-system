from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from core.utils.pagination import paginate_queryset
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
def vacancy_board_detail(request, id):
    vacancy = get_object_or_404(
        Vacancy,
        id=id,
        status__in=[VacancyStatus.PUBLISHED, VacancyStatus.CLOSED]
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

    # 🔹 fetch uploaded documents
    resume = ApplicantDocument.objects.filter(
        applicant=profile,
        document_type=ApplicantDocument.DOCUMENT_RESUME
    ).first()

    grade8 = ApplicantDocument.objects.filter(
        applicant=profile,
        document_type=ApplicantDocument.DOCUMENT_GRADE_8
    ).first()

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

    edit_id = request.GET.get("edit_id")
    instance = None

    # EDIT MODE
    if edit_id:
        instance = get_object_or_404(
            EducationQualification,
            id=edit_id,
            profile=profile
        )

    if request.method == 'POST':
        qualification_id = request.POST.get("qualification_id")

        if qualification_id:
            instance = get_object_or_404(
                EducationQualification,
                id=qualification_id,
                profile=profile
            )

        form = EducationQualificationForm(
            request.POST,
            request.FILES,
            instance=instance
        )

        if form.is_valid():
            obj = form.save(commit=False)
            obj.profile = profile
            obj.save()

            return redirect('applicant:profile_step3')

    else:
        form = EducationQualificationForm(instance=instance)

    return render(request, 'applicant/profile_step3.html', {
        'form': form,
        'profile': profile,
        'qualifications': profile.qualifications.all(),
        'edit_mode': instance is not None,
        'edit_instance': instance,
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
        status__in=[VacancyStatus.PUBLISHED, VacancyStatus.CLOSED]
    ).order_by('-announcement_date')
    pagination = paginate_queryset(request, vacancies, per_page=10)

    return render(request, 'applicant/vacancy_board_list.html', {
        'vacancies': pagination['page_obj'],
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
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


@login_required
def exam_dashboard(request):
    from examinations.models import ExamSession

    # Show only published exam sessions assigned to this applicant.
    sessions = ExamSession.objects.filter(
        applicant=request.user,
        exam__is_published=True
    ).select_related('exam', 'application')

    # Display active exams first, then upcoming exams, then finished exams.
    def sort_key(session):
        status = session.current_status
        if status == ExamSession.STATUS_ACTIVE:
            return 0
        if status == ExamSession.STATUS_NOT_STARTED:
            return 1
        return 2

    sessions = sorted(sessions, key=sort_key)

    return render(request, 'applicant/exam_dashboard.html', {
        'sessions': sessions,
    })


class ApplicantPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'applicant/change_password.html'
    success_url = reverse_lazy('applicant:dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'Password changed successfully.')
        return super().form_valid(form)