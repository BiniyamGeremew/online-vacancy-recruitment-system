from django.contrib import admin
from django.urls import path, include
from accounts.views import ApplicantLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('applicant/', include('applicant.urls')),
    path('', ApplicantLoginView.as_view(), name='home'),  # root URL
]
