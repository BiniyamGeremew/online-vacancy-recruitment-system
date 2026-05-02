from django.urls import path

from .views import (
    ApplicantPasswordChangeView,
    dashboard,
    edit_profile,
    profile_step1,
    profile_step2,
    profile_step3,
    profile_step4,
    vacancy_board_detail,
    vacancy_board_list,
    apply,
    exam_dashboard
)
from examinations.views import take_exam, exam_result

app_name = 'applicant'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('dashboard/', dashboard, name='dashboard'),

    path('profile/step1/', profile_step1, name='profile_step1'),
    path('profile/step2/', profile_step2, name='profile_step2'),
    path('profile/step3/', profile_step3, name='profile_step3'),
    path('profile/step4/', profile_step4, name='profile_step4'),

    path('vacancies/', vacancy_board_list, name='vacancy_board_list'),
    path('vacancies/<int:id>/', vacancy_board_detail, name='vacancy_board_detail'),

    path('edit-profile/', edit_profile, name='edit_profile'),
    path('change-password/', ApplicantPasswordChangeView.as_view(), name='change_password'),

    path('apply/<int:position_id>/', apply, name='apply'),
    path('exams/', exam_dashboard, name='exam_dashboard'),
    path('exam/<int:session_id>/', take_exam, name='take_exam'),
    path('exam/<int:session_id>/result/', exam_result, name='exam_result'),
]