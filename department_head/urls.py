from django.urls import path
from . import views
from examinations.views import create_exam, exam_sessions, department_head_exam_results, ai_review_questions

app_name = 'department_head'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('requests/submit/', views.SubmitEmployeeRequestView.as_view(), name='submit_request'),
    path('requests/', views.MyEmployeeRequestsView.as_view(), name='my_requests'),
    path('requests/<int:pk>/', views.EmployeeRequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/edit/', views.UpdateEmployeeRequestView.as_view(), name='request_update'),
    path('requests/<int:pk>/delete/', views.DeleteEmployeeRequestView.as_view(), name='request_delete'),
    path('requests/approved/', views.ApprovedEmployeeRequestsView.as_view(), name='approved_requests'),
    path('requests/rejected/', views.RejectedEmployeeRequestsView.as_view(), name='rejected_requests'),
    path('requests/rejected/<int:pk>/', views.EmployeeRequestDetailView.as_view(template_name='department_head/rejected_request_detail.html'), name='rejected_request_detail'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.DepartmentHeadProfileUpdateView.as_view(), name='edit_profile'),
    path('profile/change-password/', views.DepartmentHeadPasswordChangeView.as_view(), name='change_password'),
    path('generate-request-draft/', views.generate_request_draft, name='generate_request_draft'),

    path('vacancy/<int:vacancy_id>/create_exam/', create_exam, name='create_exam'),
    path('exam/<int:exam_id>/ai_review/', ai_review_questions, name='ai_review'),
    path('exam/<int:exam_id>/sessions/', exam_sessions, name='exam_sessions'),
    path('vacancy/<int:vacancy_id>/exam_results/', department_head_exam_results, name='exam_results'),
]
