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
    path('vacancy/<int:id>/close/', views.close_vacancy, name='close_vacancy'),
    path('vacancy/<int:vacancy_id>/applications/', views.vacancy_applications, name='vacancy_applications'),
]