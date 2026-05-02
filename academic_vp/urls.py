from django.urls import path
from . import views

app_name = 'academic_vp'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('pending/', views.PendingRequestsView.as_view(), name='pending_requests'),
    path('sent/', views.SentRequestsView.as_view(), name='sent_requests'),
    path('rejected/', views.RejectedRequestsView.as_view(), name='rejected_requests'),
    path('request/<int:pk>/', views.RequestDetailView.as_view(), name='request_detail'),
    path('request/<int:pk>/approve/', views.ApproveRequestView.as_view(), name='approve_request'),
    path('request/<int:pk>/reject/', views.RejectRequestView.as_view(), name='reject_request'),
    path('request/<int:pk>/forward/', views.ForwardRequestView.as_view(), name='forward_request'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.AcademicVPProfileUpdateView.as_view(), name='edit_profile'),
    path('profile/change-password/', views.AcademicVPPasswordChangeView.as_view(), name='change_password'),
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
]