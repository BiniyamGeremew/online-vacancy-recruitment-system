from django.urls import path

from .views import (
    ApplicantPasswordChangeView,
    apply_jobs,
    applications,
    dashboard,
    edit_profile,
    profile_step1,
    profile_step2,
    profile_step3,
    profile_step4,
)

app_name = 'applicant'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/step1/', profile_step1, name='profile_step1'),
    path('profile/step2/', profile_step2, name='profile_step2'),
    path('profile/step3/', profile_step3, name='profile_step3'),
    path('profile/step4/', profile_step4, name='profile_step4'),
    path('apply-jobs/', apply_jobs, name='apply_jobs'),
    path('applications/', applications, name='applications'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('change-password/', ApplicantPasswordChangeView.as_view(), name='change_password'),
]
