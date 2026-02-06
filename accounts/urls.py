from django.urls import path
from .views import CustomLoginView, CustomLogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

     path('register/', views.register_view, name='register'),
    path('activate/<uid>/<token>/', views.activate_account, name='activate'),
]
