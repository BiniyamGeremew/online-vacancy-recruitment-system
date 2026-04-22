from datetime import datetime

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from django.utils import timezone

from .models import Vacancy, VacancyPosition, JobApplication, HRAction
from department_head.models import EmployeeRequest
from organization.constants import RequestStatus
from .constants import VacancyStatus

from .vacancy_generator import generate_vacancy_text


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

    return render(request, 'hr_officer/vacancy_list.html', {
        'vacancies': vacancies
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
        announcement_date = parse_date(request.POST.get("announcement_date"))
        deadline = parse_date(request.POST.get("deadline"))

        application_instructions = request.POST.get("application_instructions")
        generated_vacancy = request.POST.get("generated_vacancy")

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
                "announcement_date": announcement_date,
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


@hr_officer_required
def vacancy_applications(request, vacancy_id):

    vacancy = get_object_or_404(Vacancy, id=vacancy_id)

    applications = JobApplication.objects.filter(
        vacancy_position__vacancy=vacancy
    ).select_related("applicant", "applicant_profile")

    return render(request, 'hr_officer/vacancy_applications.html', {
        'vacancy': vacancy,
        'applications': applications
    })


@login_required
def close_vacancy(request, id):

    vacancy = get_object_or_404(Vacancy, id=id)

    vacancy.status = VacancyStatus.CLOSED
    vacancy.save()

    messages.success(request, "Vacancy closed successfully.")

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

    return render(request, 'hr_officer/requests_list.html', {
        'requests': requests
    })


@login_required
def request_detail(request, pk):

    req = get_object_or_404(EmployeeRequest, pk=pk)

    return render(request, 'hr_officer/request_detail.html', {
        'request_obj': req,
        'actions': req.hr_actions.all()
    })