from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404

from .models import VPProfile
from department_head.models import EmployeeRequest


class AcademicVPRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        profile = getattr(user, 'vpprofile', None)
        if not profile:
            return False
        # Ensure membership in group
        return user.groups.filter(name='academic_vp').exists()

    def get_vp_profile(self):
        return getattr(self.request.user, 'vpprofile', None)

    def get_forwarded_requests(self):
        profile = self.get_vp_profile()
        if not profile or not profile.user:
            return EmployeeRequest.objects.none()
        # Filter requests forwarded to VP
        return EmployeeRequest.objects.filter(status=EmployeeRequest.STATUS_FORWARDED_TO_VP, department__college=profile.user.userprofile.department.college if getattr(profile.user, 'userprofile', None) else None)
