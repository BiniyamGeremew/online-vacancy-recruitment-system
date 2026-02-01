from django.urls import path
from .views import dashboard

app_name = 'hr_officer'

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
]
