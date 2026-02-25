from django.urls import path
from . import views

app_name = 'department_head'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
]
