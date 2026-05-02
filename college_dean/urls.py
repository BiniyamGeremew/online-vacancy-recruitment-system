from django.urls import path
from . import views

app_name = 'college_dean'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('pending/', views.PendingRequestsView.as_view(), name='pending_requests'),
    path('request/<int:pk>/', views.RequestDetailView.as_view(), name='request_detail'),
    path('request/<int:pk>/reject/', views.reject_request, name='reject_request'),
    path('request/<int:pk>/forward/', views.forward_request, name='forward_request'),
    path('sent/', views.SentRequestsView.as_view(), name='sent_requests'),
    path('notifications/', views.notifications, name='notifications'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.CollegeDeanProfileUpdateView.as_view(), name='edit_profile'),
    path('profile/change-password/', views.CollegeDeanPasswordChangeView.as_view(), name='change_password'),
    path('rejected/', views.RejectedRequestsView.as_view(), name='rejected_requests'),
]
