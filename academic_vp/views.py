from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from .mixins import AcademicVPRequiredMixin
from core.utils.pagination import PaginationMixin
from .forms import (
    ApproveRequestForm,
    RejectRequestForm,
    ForwardRequestForm,
    AcademicVPUserForm,
    AcademicVPProfileForm,
)
from .models import VPAction, VPProfile

from department_head.models import EmployeeRequest
from organization.constants import RequestStatus


class DashboardView(AcademicVPRequiredMixin, TemplateView):
    template_name = 'academic_vp/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        pending_qs = EmployeeRequest.objects.filter(
            status=RequestStatus.FORWARDED_TO_VP
        )

        ctx['pending'] = pending_qs.count()

        ctx['approved'] = EmployeeRequest.objects.filter(
            status=RequestStatus.APPROVED_BY_VP
        ).count()

        ctx['rejected'] = EmployeeRequest.objects.filter(
            status=RequestStatus.REJECTED_BY_VP
        ).count()

        ctx['forwarded'] = VPAction.objects.filter(
            performed_by=self.request.user,
            action=VPAction.ACTION_FORWARDED
        ).count()

        return ctx

class PendingRequestsView(AcademicVPRequiredMixin, PaginationMixin, ListView):
    model = EmployeeRequest
    template_name = 'academic_vp/pending_requests.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        return EmployeeRequest.objects.filter(
            status=RequestStatus.FORWARDED_TO_VP
        ).order_by('-date_submitted')

class RequestDetailView(AcademicVPRequiredMixin, DetailView):
    model = EmployeeRequest
    template_name = 'academic_vp/request_detail.html'
    context_object_name = 'request_obj'

    def get_queryset(self):
        return EmployeeRequest.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['approve_form'] = ApproveRequestForm()
        ctx['reject_form'] = RejectRequestForm()
        ctx['forward_form'] = ForwardRequestForm()
        ctx['actions'] = self.object.vp_actions.all()
        ctx['STATUS_FORWARDED_TO_VP'] = RequestStatus.FORWARDED_TO_VP
        ctx['STATUS_APPROVED_BY_VP'] = RequestStatus.APPROVED_BY_VP
        ctx['STATUS_REJECTED_BY_VP'] = RequestStatus.REJECTED_BY_VP
        ctx['STATUS_FORWARDED_TO_HR'] = RequestStatus.FORWARDED_TO_HR
        return ctx

class ApproveRequestView(AcademicVPRequiredMixin, View):
    def post(self, request, pk):
        req = get_object_or_404(
            EmployeeRequest,
            pk=pk,
            status=RequestStatus.FORWARDED_TO_VP
        )

        form = ApproveRequestForm(request.POST)
        if form.is_valid():
            VPAction.objects.create(
                request=req,
                action=VPAction.ACTION_APPROVED,
                performed_by=request.user
            )

            req.status = RequestStatus.APPROVED_BY_VP
            req.save()

            messages.success(request, 'Request approved by VP.')
            return redirect('academic_vp:pending_requests')

        messages.error(request, 'Invalid approval submission.')
        return redirect('academic_vp:request_detail', pk=pk)

class RejectRequestView(AcademicVPRequiredMixin, View):
    def post(self, request, pk):
        req = get_object_or_404(
            EmployeeRequest,
            pk=pk,
            status=RequestStatus.FORWARDED_TO_VP
        )

        form = RejectRequestForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data.get('rejection_reason')

            VPAction.objects.create(
                request=req,
                action=VPAction.ACTION_REJECTED,
                comment=reason,
                performed_by=request.user
            )

            req.status = RequestStatus.REJECTED_BY_VP
            req.save()

            messages.success(request, 'Request rejected by VP.')
            return redirect('academic_vp:pending_requests')

        messages.error(request, 'Invalid rejection submission.')
        return redirect('academic_vp:request_detail', pk=pk)

class ForwardRequestView(AcademicVPRequiredMixin, View):
    def post(self, request, pk):
        req = get_object_or_404(
            EmployeeRequest,
            pk=pk,
            status=RequestStatus.FORWARDED_TO_VP
        )

        form = ForwardRequestForm(request.POST)
        if form.is_valid():
            comment = form.cleaned_data.get('comment')

            VPAction.objects.create(
                request=req,
                action=VPAction.ACTION_FORWARDED,
                comment=comment,
                performed_by=request.user
            )

            req.status = RequestStatus.FORWARDED_TO_HR
            req.save()

            messages.success(request, 'Request forwarded to HR.')
            return redirect('academic_vp:pending_requests')

        messages.error(request, 'Invalid forward submission.')
        return redirect('academic_vp:request_detail', pk=pk)

class SentRequestsView(AcademicVPRequiredMixin, PaginationMixin, ListView):
    model = VPAction
    template_name = 'academic_vp/sent_requests.html'
    context_object_name = 'actions'
    paginate_by = 10

    def get_queryset(self):
        return VPAction.objects.filter(
            performed_by=self.request.user,
            action=VPAction.ACTION_FORWARDED
        ).order_by('-performed_at')

class RejectedRequestsView(AcademicVPRequiredMixin, PaginationMixin, ListView):
    model = EmployeeRequest
    template_name = 'academic_vp/rejected_requests.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        return EmployeeRequest.objects.filter(
            status=RequestStatus.REJECTED_BY_VP
        ).order_by('-date_submitted')

class ProfileView(AcademicVPRequiredMixin, TemplateView):
    template_name = 'academic_vp/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['profile'] = self.get_vp_profile()
        return ctx

class AcademicVPProfileUpdateView(AcademicVPRequiredMixin, View):
    template_name = 'academic_vp/profile_edit.html'

    def get(self, request, *args, **kwargs):
        profile = getattr(request.user, 'vpprofile', None)
        user_form = AcademicVPUserForm(instance=request.user)
        profile_form = AcademicVPProfileForm(instance=profile)
        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form,
        })

    def post(self, request, *args, **kwargs):
        profile = getattr(request.user, 'vpprofile', None)
        user_form = AcademicVPUserForm(request.POST, instance=request.user)
        profile_form = AcademicVPProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('academic_vp:profile')

        return render(request, self.template_name, {
            'user_form': user_form,
            'profile_form': profile_form,
        })


class AcademicVPPasswordChangeView(AcademicVPRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'academic_vp/change_password.html'
    success_url = reverse_lazy('academic_vp:profile')

    def form_valid(self, form):
        messages.success(self.request, 'Password changed successfully.')
        return super().form_valid(form)


class NotificationsView(AcademicVPRequiredMixin, TemplateView):
    template_name = 'academic_vp/notifications.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['items'] = VPAction.objects.filter(
            performed_by=self.request.user
        ).order_by('-performed_at')[:20]
        return ctx