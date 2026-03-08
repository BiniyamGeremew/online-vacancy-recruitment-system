from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('applicant/', include('applicant.urls', namespace='applicant')),
    path('hr_officer/', include('hr_officer.urls', namespace='hr_officer')),
    path('department_head/', include('department_head.urls', namespace='department_head')),
    path('college_dean/', include('college_dean.urls', namespace='college_dean')),
    path('academic_vp/', include('academic_vp.urls', namespace='academic_vp')),
    path('', RedirectView.as_view(url='/accounts/login/')),  

    path('captcha/', include('captcha.urls')), 
]
