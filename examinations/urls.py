from django.urls import path
from . import views

app_name = 'examinations'

urlpatterns = [
    path('session/<int:session_id>/security-event/', views.exam_security_event, name='exam_security_event'),
]