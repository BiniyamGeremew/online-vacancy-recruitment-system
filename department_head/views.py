from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.views import View
from django.contrib import messages
from django.http import HttpResponseForbidden

from .forms import (
    EmployeeRequestForm,
    EmployeeRequestItemFormset,
    EmployeeRequestItemFormsetCreate,
)
from .models import EmployeeRequest
from organization.constants import RequestStatus


@login_required
def dashboard(request):
    return render(request, 'department_head/dashboard.html')


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

        if self.request.method == 'POST':
            context['formset'] = EmployeeRequestItemFormset(
                self.request.POST, instance=self.object
            )
        else:
            context['formset'] = EmployeeRequestItemFormset(instance=self.object)

        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()

        formset = EmployeeRequestItemFormset(self.request.POST, instance=instance)

        if formset.is_valid():
            formset.save()
            messages.success(self.request, 'Request updated successfully.')
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