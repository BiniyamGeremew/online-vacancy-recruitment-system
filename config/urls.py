from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('applicant/', include('applicant.urls', namespace='applicant')),
    path('hr_officer/', include('hr_officer.urls', namespace='hr_officer')),
    path('', RedirectView.as_view(url='/accounts/login/')),  
]
