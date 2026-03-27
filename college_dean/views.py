from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView

from .models import DeanProfile, DeanAction
from department_head.models import EmployeeRequest
from organization.constants import RequestStatus

from .forms import RejectForm, ForwardForm


class CollegeDeanRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        profile = getattr(user, 'deanprofile', None)
        if profile and profile.college:
            return True
        return user.groups.filter(name='college_dean').exists()


@login_required
def dashboard(request):
    user = request.user
    profile = getattr(user, 'deanprofile', None)

    if not profile:
        profile = DeanProfile.objects.create(user=user)

    college = profile.college

    if not college:
        pending = rejected = forwarded = 0
    else:
        qs = EmployeeRequest.objects.filter(department__college=college)

        pending = qs.filter(status=RequestStatus.SUBMITTED).count()
        rejected = qs.filter(status=RequestStatus.REJECTED_BY_DEAN).count()

        forwarded = DeanAction.objects.filter(
            request__department__college=college,
            action=DeanAction.ACTION_FORWARDED
        ).count()

    return render(request, 'college_dean/dashboard.html', {
        'pending': pending,
        'rejected': rejected,
        'forwarded': forwarded,
    })


class PendingRequestsView(CollegeDeanRequiredMixin, ListView):
    model = EmployeeRequest
    template_name = 'college_dean/pending_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        profile = getattr(self.request.user, 'deanprofile', None)
        if not profile or not profile.college:
            return EmployeeRequest.objects.none()

        return EmployeeRequest.objects.filter(
            department__college=profile.college,
            status=RequestStatus.SUBMITTED
        ).order_by('-date_submitted')


class RequestDetailView(CollegeDeanRequiredMixin, DetailView):
    model = EmployeeRequest
    template_name = 'college_dean/request_detail.html'
    context_object_name = 'request_obj'

    def get_queryset(self):
        profile = getattr(self.request.user, 'deanprofile', None)
        if not profile or not profile.college:
            return EmployeeRequest.objects.none()

        return EmployeeRequest.objects.filter(
            department__college=profile.college
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['reject_form'] = RejectForm()
        ctx['forward_form'] = ForwardForm()
        ctx['actions'] = self.object.dean_actions.all()
        return ctx


def _ensure_dean_of_request(user, request_obj):
    profile = getattr(user, 'deanprofile', None)
    return (
        profile
        and profile.college
        and request_obj.department.college_id == profile.college_id
    )


def _record_action_and_update(request_obj, user, action, reason=''):
    DeanAction.objects.create(
        request=request_obj,
        action=action,
        reason=reason,
        performed_by=user
    )

    if action == DeanAction.ACTION_REJECTED:
        request_obj.status = RequestStatus.REJECTED_BY_DEAN
    elif action == DeanAction.ACTION_FORWARDED:
        request_obj.status = RequestStatus.FORWARDED_TO_VP

    request_obj.save()


@login_required
def reject_request(request, pk):
    req = get_object_or_404(EmployeeRequest, pk=pk)

    if not _ensure_dean_of_request(request.user, req):
        messages.error(request, 'Permission denied.')
        return redirect('college_dean:pending_requests')

    if request.method == 'POST':
        form = RejectForm(request.POST)
        if form.is_valid():
            _record_action_and_update(
                req,
                request.user,
                DeanAction.ACTION_REJECTED,
                reason=form.cleaned_data.get('reason')
            )
            messages.success(request, 'Request rejected.')
            return redirect('college_dean:pending_requests')

    return redirect('college_dean:request_detail', pk=pk)


@login_required
def forward_request(request, pk):
    req = get_object_or_404(EmployeeRequest, pk=pk)

    if not _ensure_dean_of_request(request.user, req):
        messages.error(request, 'Permission denied.')
        return redirect('college_dean:pending_requests')

    if request.method == 'POST':
        form = ForwardForm(request.POST)
        if form.is_valid():
            _record_action_and_update(
                req,
                request.user,
                DeanAction.ACTION_FORWARDED,
                reason=form.cleaned_data.get('reason')
            )
            messages.success(request, 'Request forwarded to VP.')
            return redirect('college_dean:pending_requests')

    return redirect('college_dean:request_detail', pk=pk)


class SentRequestsView(CollegeDeanRequiredMixin, ListView):
    model = DeanAction
    template_name = 'college_dean/sent_requests.html'
    context_object_name = 'actions'

    def get_queryset(self):
        return DeanAction.objects.filter(
            performed_by=self.request.user
        ).order_by('-performed_at')


class RejectedRequestsView(CollegeDeanRequiredMixin, ListView):
    model = EmployeeRequest
    template_name = 'college_dean/rejected_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        profile = getattr(self.request.user, 'deanprofile', None)
        if not profile or not profile.college:
            return EmployeeRequest.objects.none()

        return EmployeeRequest.objects.filter(
            department__college=profile.college,
            status=RequestStatus.REJECTED_BY_DEAN
        ).order_by('-date_submitted')

@login_required
def notifications(request):
    profile = getattr(request.user, 'deanprofile', None)

    items = []
    if profile and profile.college:
        items = DeanAction.objects.filter(
            request__department__college=profile.college
        ).order_by('-performed_at')[:20]

    return render(request, 'college_dean/notifications.html', {
        'items': items
    })


@login_required
def profile(request):
    profile = getattr(request.user, 'deanprofile', None)
    return render(request, 'college_dean/profile.html', {
        'profile': profile
    })