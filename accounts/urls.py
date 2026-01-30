from django.urls import path
from .views import ApplicantLoginView

urlpatterns = [
    path('login/', ApplicantLoginView.as_view(), name='login'),
]
