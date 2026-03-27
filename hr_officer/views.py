from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count

from department_head.models import EmployeeRequest
from .models import HRAction
from organization.constants import RequestStatus


@login_required
def dashboard(request):
    user = request.user

    total_requests = EmployeeRequest.objects.filter(
        hr_actions__performed_by=user
    ).distinct().count()

    vacancy_count = HRAction.objects.filter(
        action=HRAction.ACTION_VACANCY
    ).count()

    screening_count = HRAction.objects.filter(
        action=HRAction.ACTION_SCREENING
    ).count()

    interview_count = HRAction.objects.filter(
        action=HRAction.ACTION_INTERVIEW
    ).count()

    hired_count = HRAction.objects.filter(
        action=HRAction.ACTION_HIRED
    ).count()

    context = {
        'total_requests': total_requests,
        'vacancy_count': vacancy_count,
        'screening_count': screening_count,
        'interview_count': interview_count,
        'hired_count': hired_count,
    }

    return render(request, 'hr_officer/dashboard.html', context)


@login_required
def hr_requests_list(request):
    """
    Show requests that reached HR stage (forwarded to VP or beyond)
    """
    requests = EmployeeRequest.objects.filter(
        status=RequestStatus.FORWARDED_TO_VP
    ).order_by('-date_submitted')

    return render(request, 'hr_officer/requests_list.html', {
        'requests': requests
    })


@login_required
def request_detail(request, pk):
    req = get_object_or_404(EmployeeRequest, pk=pk)

    actions = req.hr_actions.all()

    return render(request, 'hr_officer/request_detail.html', {
        'request_obj': req,
        'actions': actions
    })

@login_required
def add_hr_action(request, pk):
    req = get_object_or_404(EmployeeRequest, pk=pk)

    if request.method == 'POST':
        action_type = request.POST.get('action')
        note = request.POST.get('note', '')

        if action_type:
            HRAction.objects.create(
                request=req,
                action=action_type,
                note=note,
                performed_by=request.user
            )

            messages.success(request, 'HR action recorded successfully.')
            return redirect('hr_officer:request_detail', pk=req.pk)

    return render(request, 'hr_officer/add_action.html', {
        'request_obj': req,
        'action_choices': HRAction.ACTION_CHOICES
    })


@login_required
def my_actions(request):
    actions = HRAction.objects.filter(
        performed_by=request.user
    ).order_by('-performed_at')

    return render(request, 'hr_officer/my_actions.html', {
        'actions': actions
    })