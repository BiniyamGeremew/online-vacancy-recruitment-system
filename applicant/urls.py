from django.urls import path
from .views import dashboard

app_name = 'applicant'

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
]
