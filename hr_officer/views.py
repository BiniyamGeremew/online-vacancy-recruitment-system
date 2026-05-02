from datetime import datetime

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from core.utils.pagination import paginate_queryset

from .models import HRProfile, Vacancy, VacancyPosition, JobApplication, HRAction
from .forms import HROfficerUserForm, HRProfileForm
from department_head.models import EmployeeRequest
from organization.constants import RequestStatus
from .constants import VacancyStatus
from applications.models import Application

from .vacancy_generator import generate_vacancy_text
from notifications.services import notify_matching_applicants_for_vacancy, send_screening_update_notification, send_email_notification
from notifications.models import Notification


def hr_officer_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and u.groups.filter(name='hr_officer').exists()
    )(view_func)


def parse_date(value):
    if not value or value.strip() == "":
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


@login_required
def vacancy_list(request):
    vacancies = Vacancy.objects.all().order_by('-announcement_date')
    pagination = paginate_queryset(request, vacancies, per_page=10)

    return render(request, 'hr_officer/vacancy_list.html', {
        'vacancies': pagination['page_obj'],
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
    })


@login_required
def create_vacancy(request, request_id):

    employee_request = get_object_or_404(EmployeeRequest, pk=request_id)

    if hasattr(employee_request, 'vacancy'):
        messages.warning(request, "Vacancy already exists.")
        return redirect('hr_officer:vacancy_detail', id=employee_request.vacancy.id)

    generated_vacancy = ""

    if request.method == "POST":

        action = request.POST.get("action")

        vacancy_type = request.POST.get("vacancy_type")
        experience = request.POST.get("experience")
        skills = request.POST.get("skills")
        salary_info = request.POST.get("salary_info")
        announcement_date = timezone.now().date()
        deadline = parse_date(request.POST.get("deadline"))

        application_instructions = request.POST.get("application_instructions")
        generated_vacancy = request.POST.get("generated_vacancy")

        if not deadline:
            messages.error(request, "Please enter an application deadline for the vacancy.")
            return render(request, "hr_officer/create_vacancy.html", {
                "employee_request": employee_request,
                "generated_vacancy": generated_vacancy,
                "vacancy_type": vacancy_type,
                "experience": experience,
                "skills": skills,
                "salary_info": salary_info,
                "deadline": deadline,
                "application_instructions": application_instructions,
            })

        if action == "generate":

            generated_vacancy = generate_vacancy_text(
                employee_request=employee_request,
                vacancy_type=vacancy_type,
                experience=experience,
                skills=skills,
                salary=salary_info,
                announcement_date=announcement_date,
                deadline=deadline
            )

            messages.success(request, "Vacancy generated successfully.")

            return render(request, "hr_officer/create_vacancy.html", {
                "employee_request": employee_request,
                "generated_vacancy": generated_vacancy,
                "vacancy_type": vacancy_type,
                "experience": experience,
                "skills": skills,
                "salary_info": salary_info,
                "deadline": deadline,
                "application_instructions": application_instructions
            })

        if action == "publish":

            vacancy = Vacancy.objects.create(
                employee_request=employee_request,
                vacancy_type=vacancy_type,
                experience_requirement=experience,
                required_skills=skills,
                salary_info=salary_info,
                announcement_text=generated_vacancy,
                application_instructions=application_instructions,
                announcement_date=announcement_date,
                deadline=deadline,
                posted_by=request.user,
                status=VacancyStatus.PUBLISHED
            )

            for item in employee_request.items.all():

                VacancyPosition.objects.create(
                    vacancy=vacancy,
                    department=employee_request.department,
                    academic_rank=item.academic_rank,
                    field_of_education=item.study_department,
                    minimum_cgpa=item.cgpa_requirement,
                    positions=item.number_of_employees
                )

            employee_request.status = RequestStatus.VACANCY
            employee_request.save()

            HRAction.objects.create(
                request=employee_request,
                action=HRAction.ACTION_VACANCY,
                performed_by=request.user,
                note="Vacancy announced."
            )

            notify_matching_applicants_for_vacancy(vacancy)

            messages.success(request, "Vacancy published successfully.")

            return redirect('hr_officer:vacancy_detail', id=vacancy.id)

    return render(request, 'hr_officer/create_vacancy.html', {
        'employee_request': employee_request,
        'generated_vacancy': generated_vacancy
    })


@login_required
def vacancy_detail(request, id):

    vacancy = get_object_or_404(Vacancy, id=id)

    return render(request, 'hr_officer/vacancy_detail.html', {
        'vacancy': vacancy,
        'positions': vacancy.positions.all()
    })


def _get_hr_profile(user):
    try:
        return user.hrprofile
    except HRProfile.DoesNotExist:
        return None


@login_required
@hr_officer_required
def profile_view(request):
    profile = _get_hr_profile(request.user)
    return render(request, 'hr_officer/profile.html', {
        'profile': profile,
    })


@login_required
@hr_officer_required
def edit_profile(request):
    profile, _ = HRProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = HROfficerUserForm(request.POST, instance=request.user)
        profile_form = HRProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('hr_officer:profile')
    else:
        user_form = HROfficerUserForm(instance=request.user)
        profile_form = HRProfileForm(instance=profile)

    return render(request, 'hr_officer/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
@hr_officer_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('hr_officer:profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'hr_officer/change_password.html', {
        'form': form,
    })


@hr_officer_required
def all_applications(request):

    applications = Application.objects.all().select_related("applicant__user", "position__vacancy").order_by('-submitted_at')
    pagination = paginate_queryset(request, applications, per_page=5)

    return render(request, 'hr_officer/all_applications.html', {
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
    })


@hr_officer_required
def screening_redirect(request):
    messages.info(request, 'Please select a vacancy to screen candidates.')
    return redirect('hr_officer:vacancy_list')


@hr_officer_required
def vacancy_screening(request, vacancy_id):
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)
    filter_option = request.GET.get('filter', 'all')

    base_queryset = Application.objects.filter(position__vacancy=vacancy).select_related("applicant__user", "position__vacancy")

    if filter_option == 'eligible':
        applications = base_queryset.filter(status=Application.STATUS_ELIGIBLE).order_by('-ranking_score', '-submitted_at')
    elif filter_option == 'ineligible':
        applications = base_queryset.filter(status=Application.STATUS_REJECTED).order_by('-ranking_score', '-submitted_at')
    elif filter_option == 'submitted':
        applications = base_queryset.filter(status=Application.STATUS_SUBMITTED).order_by('-ranking_score', '-submitted_at')
    else:
        applications = base_queryset.filter(
            status__in=[
                Application.STATUS_SUBMITTED,
                Application.STATUS_ELIGIBLE,
                Application.STATUS_REJECTED
            ]
        ).order_by('-ranking_score', '-submitted_at')

    counts = {
        'eligible': base_queryset.filter(status=Application.STATUS_ELIGIBLE).count(),
        'ineligible': base_queryset.filter(status=Application.STATUS_REJECTED).count(),
        'submitted': base_queryset.filter(status=Application.STATUS_SUBMITTED).count(),
    }

    deadline_passed = vacancy.deadline and vacancy.deadline <= timezone.now().date()
    shortlist_finalized = vacancy.shortlist_finalized
    can_shortlist = deadline_passed and not shortlist_finalized

    if request.method == 'POST':
        application_id = request.POST.get('application_id')
        action = request.POST.get('action')
        application = get_object_or_404(Application, id=application_id, position__vacancy=vacancy)

        if action == 'eligible':
            application.status = Application.STATUS_ELIGIBLE
        elif action == 'reject':
            application.status = Application.STATUS_REJECTED
        elif action == 'shortlist':
            if not deadline_passed:
                messages.error(request, 'Shortlisting is allowed only after the vacancy deadline has passed.')
                return redirect('hr_officer:vacancy_screening', vacancy_id=vacancy.id)
            if shortlist_finalized:
                messages.error(request, 'Shortlist is finalized and cannot be edited.')
                return redirect('hr_officer:vacancy_screening', vacancy_id=vacancy.id)
            application.status = Application.STATUS_SHORTLISTED

        application.save()
        send_screening_update_notification(application)
        messages.success(request, f"{application.applicant.user.get_full_name()} updated to {application.get_status_display()}.")
        return redirect('hr_officer:vacancy_screening', vacancy_id=vacancy.id)

    pagination = paginate_queryset(request, applications, per_page=5)

    return render(request, 'hr_officer/vacancy_screening.html', {
        'vacancy': vacancy,
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
        'filter_option': filter_option,
        'counts': counts,
        'deadline_passed': deadline_passed,
        'shortlist_finalized': shortlist_finalized,
        'can_shortlist': can_shortlist,
    })


@hr_officer_required
def vacancy_shortlist(request, vacancy_id):
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)

    applications = Application.objects.filter(
        position__vacancy=vacancy,
        status=Application.STATUS_SHORTLISTED
    ).select_related("applicant__user", "position__vacancy") \
     .order_by('-ranking_score', '-submitted_at')

    deadline_passed = vacancy.deadline and vacancy.deadline <= timezone.now().date()
    shortlist_finalized = vacancy.shortlist_finalized

    if request.method == 'POST':
        action = request.POST.get('action')

        # REMOVE candidate from shortlist
        if action == 'remove':
            application_id = request.POST.get('application_id')
            application = get_object_or_404(
                Application,
                id=application_id,
                position__vacancy=vacancy
            )

            if shortlist_finalized:
                messages.error(request, "Shortlist already finalized.")
            else:
                application.status = Application.STATUS_ELIGIBLE
                application.save()
                messages.success(request, "Candidate removed from shortlist.")

        # FINALIZE shortlist
        elif action == 'finalize':

            if not deadline_passed:
                messages.error(request, "Cannot finalize before deadline.")
            elif shortlist_finalized:
                messages.info(request, "Already finalized.")
            elif not applications.exists():
                messages.error(request, "No shortlisted candidates.")
            else:
                vacancy.shortlist_finalized = True
                vacancy.save(update_fields=['shortlist_finalized'])

                # Notify Department Head
                department_head = vacancy.employee_request.department.head
                if department_head:
                    Notification.objects.create(
                        user=department_head,
                        title='Shortlist Finalized',
                        message=f'Shortlist for vacancy "{vacancy.employee_request.subject}" has been finalized. You can now prepare the exam.',
                        link=f'/department_head/request/{vacancy.employee_request.id}/',
                        notification_type=Notification.TYPE_SHORTLIST_FINALIZED
                    )
                    # Send email notification
                    send_email_notification(
                        department_head,
                        'Shortlist Finalized - Prepare Exam',
                        f'The shortlist for vacancy "{vacancy.employee_request.subject}" has been finalized by HR Officer. Please log in to prepare the exam for the shortlisted candidates.'
                    )

                messages.success(request, "Shortlist finalized successfully.")

        return redirect('hr_officer:vacancy_shortlist', vacancy_id=vacancy.id)

    can_prepare_exam = deadline_passed and shortlist_finalized

    pagination = paginate_queryset(request, applications, per_page=5)

    return render(request, 'hr_officer/vacancy_shortlist.html', {
        'vacancy': vacancy,
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
        'deadline_passed': deadline_passed,
        'shortlist_finalized': shortlist_finalized,
        'can_prepare_exam': can_prepare_exam,
    })

@hr_officer_required
def hr_officer_exam_results(request, vacancy_id):
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)
    exam = vacancy.exams.filter(is_published=True).order_by('-created_at').first()
    sessions = exam.sessions.select_related('applicant', 'application', 'result').order_by('-start_time') if exam else []
    pagination = paginate_queryset(request, sessions, per_page=5)

    return render(request, 'examinations/exam_results_list.html', {
        'vacancy': vacancy,
        'exam': exam,
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
        'view_mode': 'hr_officer',
    })


@hr_officer_required
def application_detail(request, application_id):

    application = get_object_or_404(Application, id=application_id)

    vacancy = application.position.vacancy

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('hr_notes', '')
        score = request.POST.get('ranking_score')

        if action == 'eligible':
            application.status = Application.STATUS_ELIGIBLE
        elif action == 'shortlisted':
            if vacancy.deadline and vacancy.deadline > timezone.now().date():
                messages.error(request, 'Shortlisting is allowed only after the vacancy deadline has passed.')
                return redirect('hr_officer:application_detail', application_id=application.id)
            if vacancy.shortlist_finalized:
                messages.error(request, 'Shortlist is finalized and cannot be edited.')
                return redirect('hr_officer:application_detail', application_id=application.id)
            application.status = Application.STATUS_SHORTLISTED
        elif action == 'rejected':
            application.status = Application.STATUS_REJECTED
        elif action == 'interview':
            application.status = Application.STATUS_INTERVIEW
        elif action == 'final_selection':
            application.status = Application.STATUS_FINAL_SELECTION

        application.hr_notes = notes
        if score:
            application.ranking_score = score
        application.save()

        if application.status in {
            Application.STATUS_ELIGIBLE,
            Application.STATUS_REJECTED,
            Application.STATUS_SHORTLISTED,
        }:
            send_screening_update_notification(application)

        messages.success(request, f'Application status updated to {application.get_status_display()}.')
        return redirect('hr_officer:application_detail', application_id=application.id)

    can_shortlist = bool(vacancy.deadline and vacancy.deadline <= timezone.now().date() and not vacancy.shortlist_finalized)
    return render(request, 'hr_officer/application_detail.html', {
        'application': application,
        'can_shortlist': can_shortlist,
    })


@hr_officer_required
def vacancy_applications(request, vacancy_id):

    vacancy = get_object_or_404(Vacancy, id=vacancy_id)

    applications = Application.objects.filter(
        position__vacancy=vacancy
    ).select_related("applicant", "position").order_by('-submitted_at')

    pagination = paginate_queryset(request, applications, per_page=5)

    return render(request, 'hr_officer/vacancy_applications.html', {
        'vacancy': vacancy,
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
    })


@login_required
@hr_officer_required
def close_vacancy(request, id):
    vacancy = get_object_or_404(Vacancy, id=id)

    if vacancy.status == VacancyStatus.CLOSED:
        messages.error(request, 'Vacancy already closed.')
        return redirect('hr_officer:vacancy_detail', id=vacancy.id)

    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('hr_officer:vacancy_detail', id=vacancy.id)

    reason = request.POST.get('reason', '').strip()
    if not reason:
        messages.error(request, 'Please provide a reason for closing this vacancy.')
        return redirect('hr_officer:vacancy_detail', id=vacancy.id)

    vacancy.status = VacancyStatus.CLOSED
    vacancy.closed_reason = reason
    vacancy.closed_by = request.user
    vacancy.closed_at = timezone.now()
    vacancy.save()

    messages.success(request, 'Vacancy closed successfully.')
    return redirect('hr_officer:vacancy_detail', id=vacancy.id)


@login_required
def dashboard(request):

    total_requests = EmployeeRequest.objects.filter(
        status__in=[
            RequestStatus.FORWARDED_TO_HR,
            RequestStatus.VACANCY
        ]
    ).count()

    vacancy_count = HRAction.objects.filter(action=HRAction.ACTION_VACANCY).count()
    screening_count = HRAction.objects.filter(action=HRAction.ACTION_SCREENING).count()
    interview_count = HRAction.objects.filter(action=HRAction.ACTION_INTERVIEW).count()
    hired_count = HRAction.objects.filter(action=HRAction.ACTION_HIRED).count()

    return render(request, 'hr_officer/dashboard.html', {
        'total_requests': total_requests,
        'vacancy_count': vacancy_count,
        'screening_count': screening_count,
        'interview_count': interview_count,
        'hired_count': hired_count,
    })


@login_required
def hr_requests_list(request):

    requests = EmployeeRequest.objects.filter(
        status__in=[
            RequestStatus.FORWARDED_TO_HR,
            RequestStatus.VACANCY
        ]
    ).order_by('-date_submitted')
    pagination = paginate_queryset(request, requests, per_page=10)

    return render(request, 'hr_officer/requests_list.html', {
        'requests': pagination['page_obj'],
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
    })


@login_required
def request_detail(request, pk):

    req = get_object_or_404(EmployeeRequest, pk=pk)

    return render(request, 'hr_officer/request_detail.html', {
        'request_obj': req,
        'actions': req.hr_actions.all()
    })