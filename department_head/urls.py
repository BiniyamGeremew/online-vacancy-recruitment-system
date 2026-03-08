from django.urls import path
from . import views

app_name = 'department_head'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('requests/submit/', views.SubmitEmployeeRequestView.as_view(), name='submit_request'),
    path('requests/', views.MyEmployeeRequestsView.as_view(), name='my_requests'),
    path('requests/<int:pk>/', views.EmployeeRequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/edit/', views.UpdateEmployeeRequestView.as_view(), name='request_update'),
    path('requests/<int:pk>/delete/', views.DeleteEmployeeRequestView.as_view(), name='request_delete'),
]
