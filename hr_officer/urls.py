from django.urls import path
from . import views

app_name = 'hr_officer'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('requests/', views.hr_requests_list, name='requests'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/<int:pk>/add-action/', views.add_hr_action, name='add_action'),
    path('my-actions/', views.my_actions, name='my_actions'),
]