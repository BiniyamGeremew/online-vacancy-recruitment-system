from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.views import View
from django.http import JsonResponse

from .forms import (
    EmployeeRequestForm,
    EmployeeRequestItemFormset,
    EmployeeRequestItemFormsetCreate,
)
from .models import EmployeeRequest
from .services.ai_request_generator import generate_employee_request
from organization.constants import RequestStatus
import json
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden


@login_required
def dashboard(request):
    profile = getattr(request.user, "userprofile", None)

    if not profile or not profile.department:
        return render(request, "department_head/dashboard.html")

    department = profile.department

    qs = EmployeeRequest.objects.filter(department=department)

    context = {
        "total_requests": qs.count(),
        "submitted_count": qs.filter(status=RequestStatus.SUBMITTED).count(),
        "approved_count": qs.filter(status=RequestStatus.APPROVED_BY_DEAN).count(),
        "rejected_count": qs.filter(status=RequestStatus.REJECTED_BY_DEAN).count(),
        "forwarded_count": qs.filter(status=RequestStatus.FORWARDED_TO_VP).count(),
        "recent_requests": qs.order_by("-date_submitted")[:5],
    }

    return render(request, "department_head/dashboard.html", context)


class DepartmentHeadRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user

        profile = getattr(user, 'userprofile', None)
        if profile and profile.department and profile.department.head == user:
            return True

        from organization.models import Department
        return Department.objects.filter(head=user).exists()


class SubmitEmployeeRequestView(DepartmentHeadRequiredMixin, CreateView):
    model = EmployeeRequest
    form_class = EmployeeRequestForm
    template_name = 'department_head/submit_request.html'
    success_url = reverse_lazy('department_head:my_requests')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.method == 'POST':
            context['formset'] = EmployeeRequestItemFormsetCreate(self.request.POST)
        else:
            context['formset'] = EmployeeRequestItemFormsetCreate()

        return context

    def form_valid(self, form):
        user = self.request.user
        profile = getattr(user, 'userprofile', None)

        if not profile or not profile.department:
            form.add_error(None, 'Your profile is not linked to a department.')
            return self.form_invalid(form)

        instance = form.save(commit=False)
        instance.created_by = user
        instance.department = profile.department
        instance.status = RequestStatus.SUBMITTED
        if instance.request_narrative:
            instance.ai_generated = True
        instance.save()

        formset = EmployeeRequestItemFormsetCreate(self.request.POST, instance=instance)

        if formset.is_valid():
            formset.save()
            messages.success(self.request, 'Request submitted successfully.')
            return redirect(self.success_url)
        else:
            instance.delete()
            return self.form_invalid(form)


class MyEmployeeRequestsView(LoginRequiredMixin, ListView):
    model = EmployeeRequest
    template_name = 'department_head/my_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        profile = getattr(self.request.user, 'userprofile', None)

        if not profile or not profile.department:
            return EmployeeRequest.objects.none()

        return EmployeeRequest.objects.filter(
            department=profile.department
        ).order_by('-date_submitted')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx['STATUS_SUBMITTED'] = RequestStatus.SUBMITTED
        ctx['STATUS_APPROVED_BY_DEAN'] = RequestStatus.APPROVED_BY_DEAN
        ctx['STATUS_REJECTED_BY_DEAN'] = RequestStatus.REJECTED_BY_DEAN
        ctx['STATUS_FORWARDED_TO_VP'] = RequestStatus.FORWARDED_TO_VP

        return ctx

class EmployeeRequestDetailView(LoginRequiredMixin, DetailView):
    model = EmployeeRequest
    template_name = 'department_head/request_detail.html'
    context_object_name = 'request_obj'

    def get_queryset(self):
        profile = getattr(self.request.user, 'userprofile', None)
        if profile and profile.department:
            return EmployeeRequest.objects.filter(department=profile.department)
        return EmployeeRequest.objects.none()


class UpdateEmployeeRequestView(DepartmentHeadRequiredMixin, UpdateView):
    model = EmployeeRequest
    form_class = EmployeeRequestForm
    template_name = 'department_head/request_update.html'
    success_url = reverse_lazy('department_head:my_requests')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.status != RequestStatus.SUBMITTED:
            messages.error(request, 'Only submitted requests can be edited.')
            return redirect('department_head:request_detail', pk=obj.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['formset'] = EmployeeRequestItemFormset(self.request.POST, instance=self.object)
        else:
            context['formset'] = EmployeeRequestItemFormset(instance=self.object)

        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()

        formset = EmployeeRequestItemFormset(self.request.POST, instance=instance)

        if formset.is_valid():
            formset.save()

            action = self.request.POST.get("action")

            # 🔥 NEW: regenerate if requested
            if action == "regenerate":
                positions = []

                for item in instance.items.all():
                    positions.append({
                        "academic_qualification": item.academic_qualification,
                        "academic_rank": item.academic_rank,
                        "study_department": item.study_department,
                        "experience_years": item.experience_years,
                        "cgpa_requirement": item.cgpa_requirement,
                        "number_of_employees": item.number_of_employees,
                    })

                request_data = {
                    "department": instance.department.name,
                    "subject": instance.subject,
                    "positions": positions,
                }

                instance.request_narrative = generate_employee_request(request_data)
                instance.ai_generated = True
                instance.save()

            messages.success(self.request, "Request updated successfully.")
            return redirect(self.success_url)

        return self.form_invalid(form)


class DeleteEmployeeRequestView(DepartmentHeadRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(EmployeeRequest, pk=pk)

        profile = getattr(request.user, 'userprofile', None)

        if not profile or not profile.department or obj.department != profile.department:
            return HttpResponseForbidden()

        if obj.status != RequestStatus.SUBMITTED:
            messages.error(request, 'Only submitted requests can be deleted.')
            return redirect('department_head:request_detail', pk=obj.pk)

        obj.delete()
        messages.success(request, 'Request deleted.')
        return redirect('department_head:my_requests')


class ApprovedEmployeeRequestsView(LoginRequiredMixin, ListView):
    model = EmployeeRequest
    template_name = 'department_head/approved_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        profile = getattr(self.request.user, 'userprofile', None)

        if not profile or not profile.department:
            return EmployeeRequest.objects.none()

        return EmployeeRequest.objects.filter(
            department=profile.department,
            status=RequestStatus.APPROVED_BY_DEAN
        ).order_by('-date_submitted')


class RejectedEmployeeRequestsView(LoginRequiredMixin, ListView):
    model = EmployeeRequest
    template_name = 'department_head/rejected_request.html'
    context_object_name = 'requests'

    def get_queryset(self):
        profile = getattr(self.request.user, 'userprofile', None)

        if not profile or not profile.department:
            return EmployeeRequest.objects.none()

        return EmployeeRequest.objects.filter(
            department=profile.department,
            status=RequestStatus.REJECTED_BY_DEAN
        ).order_by('-date_submitted')


@login_required
@require_POST
def generate_request_draft(request):

    user = request.user
    profile = getattr(user, 'userprofile', None)

    if not profile or not profile.department:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    subject = data.get('subject', '')
    positions_data = data.get('positions', [])

    positions = []
    for pos in positions_data:
        positions.append({
            'academic_qualification': pos.get('academic_qualification', ''),
            'academic_rank': pos.get('academic_rank', ''),
            'study_department': pos.get('study_department', ''),
            'experience_years': pos.get('experience_years', 0),
            'cgpa_requirement': pos.get('cgpa_requirement', ''),
            'number_of_employees': pos.get('number_of_employees', 1),
        })

    request_data = {
        'department': profile.department.name,
        'subject': subject,
        'positions': positions,
    }

    narrative = generate_employee_request(request_data)

    return JsonResponse({'narrative': narrative})