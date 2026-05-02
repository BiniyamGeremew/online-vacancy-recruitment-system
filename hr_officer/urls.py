from django.urls import path
from . import views

app_name = 'hr_officer'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('requests/', views.hr_requests_list, name='requests_list'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('vacancy/list/', views.vacancy_list, name='vacancy_list'),
    path('vacancy/create/<int:request_id>/', views.create_vacancy, name='create_vacancy'),
    path('vacancy/<int:id>/', views.vacancy_detail, name='vacancy_detail'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('vacancy/<int:id>/close/', views.close_vacancy, name='close_vacancy'),
    path('vacancy/<int:vacancy_id>/applications/', views.vacancy_applications, name='vacancy_applications'),
    path('vacancy/<int:vacancy_id>/screening/', views.vacancy_screening, name='vacancy_screening'),
    path('vacancy/<int:vacancy_id>/shortlist/', views.vacancy_shortlist, name='vacancy_shortlist'),
    path('vacancy/<int:vacancy_id>/exam_results/', views.hr_officer_exam_results, name='exam_results'),
    path('screening/', views.screening_redirect, name='screening_redirect'),
    path('applications/', views.all_applications, name='all_applications'),
    path('application/<int:application_id>/', views.application_detail, name='application_detail'),
]