from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.groups.filter(name='applicant').exists():
            return reverse_lazy('applicant:dashboard')
        elif user.groups.filter(name='hr_officer').exists():
            return reverse_lazy('hr_officer:dashboard')
        
        return reverse_lazy('accounts:login')  

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')
