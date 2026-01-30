from django.contrib.auth.views import LoginView

class ApplicantLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    next_page = '/applicant/dashboard/'  