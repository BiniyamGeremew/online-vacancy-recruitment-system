from django.urls import path

from . import views

app_name = 'applications'

urlpatterns = [
    path('apply/<int:position_id>/', views.apply, name='apply'),
    path('my-applications/', views.my_applications, name='my_applications'),
]