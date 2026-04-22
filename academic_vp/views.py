from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib import messages

from .mixins import AcademicVPRequiredMixin
from .forms import ApproveRequestForm, RejectRequestForm, ForwardRequestForm
from .models import VPAction

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

class PendingRequestsView(AcademicVPRequiredMixin, ListView):
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

class SentRequestsView(AcademicVPRequiredMixin, ListView):
    model = VPAction
    template_name = 'academic_vp/sent_requests.html'
    context_object_name = 'actions'

    def get_queryset(self):
        return VPAction.objects.filter(
            performed_by=self.request.user,
            action=VPAction.ACTION_FORWARDED
        ).order_by('-performed_at')

class RejectedRequestsView(AcademicVPRequiredMixin, ListView):
    model = EmployeeRequest
    template_name = 'academic_vp/rejected_requests.html'
    context_object_name = 'requests'

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

class NotificationsView(AcademicVPRequiredMixin, TemplateView):
    template_name = 'academic_vp/notifications.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['items'] = VPAction.objects.filter(
            performed_by=self.request.user
        ).order_by('-performed_at')[:20]
        return ctx