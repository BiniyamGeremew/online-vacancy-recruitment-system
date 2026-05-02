from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import models

from core.utils.pagination import paginate_queryset
from hr_officer.models import VacancyPosition
from hr_officer.constants import VacancyStatus
from applicant.models import ApplicantProfile

from .models import Application
from .services import ScreeningService
from notifications.services import send_submission_notifications, send_screening_update_notification


@login_required
def apply(request, position_id):
    user = request.user
    profile, _ = ApplicantProfile.objects.get_or_create(user=user)

    position = get_object_or_404(
        VacancyPosition,
        id=position_id,
        vacancy__status=VacancyStatus.PUBLISHED
    )

    vacancy = position.vacancy

    if vacancy.deadline and vacancy.deadline < timezone.now().date():
        messages.warning(request, 'The application deadline has passed.')
        return redirect('applicant:vacancy_board_detail', id=vacancy.id)

    # Check if already applied
    if Application.objects.filter(applicant=profile, position=position).exists():
        messages.warning(request, 'You have already applied for this position.')
        return redirect('applicant:vacancy_board_detail', id=vacancy.id)

    # Check if profile is complete
    if not profile.profile_is_complete():
        messages.warning(request, 'Please complete your profile before applying.')
        return redirect('applicant:edit_profile')

    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '')

        # Run eligibility check
        is_eligible, rejection_reason = ScreeningService.check_eligibility(profile, position)

        if not is_eligible:
            messages.warning(request, rejection_reason)
            return redirect('applicant:vacancy_board_detail', id=vacancy.id)

        # Create application
        application = Application.objects.create(
            applicant=profile,
            position=position,
            status=Application.STATUS_SUBMITTED,
            cover_letter=cover_letter,
        )

        try:
            # Process through ATS pipeline
            ranking_score, ai_summary = ScreeningService.process_application(application)

            # Update application with results
            application.ranking_score = ranking_score
            application.ai_summary = ai_summary
            application.save()

            messages.success(request, f'Application submitted successfully! Your application is under review.')

        except Exception as e:
            # If ATS processing fails, still save application but with default score
            application.ranking_score = Decimal('0.00')
            application.ai_summary = f"Error during automated screening: {str(e)}"
            application.save()
            messages.warning(request, 'Application submitted but automated screening encountered an error. HR will review manually.')

        send_submission_notifications(application)

        return redirect('applications:my_applications')

    # Prepare data for review
    context = {
        'profile': profile,
        'user': user,
        'position': position,
        'vacancy': vacancy,
        'education': profile.qualifications.all(),
        'employment': profile.employments.all(),
        'documents': profile.documents.all(),
    }

    return render(request, 'applications/application_review.html', context)


@login_required
def my_applications(request):
    try:
        profile = request.user.applicant_profile
    except ApplicantProfile.DoesNotExist:
        messages.warning(request, 'Please complete your profile first.')
        return redirect('applicant:edit_profile')

    applications = Application.objects.filter(applicant=profile).select_related('position__vacancy').order_by('-submitted_at')
    pagination = paginate_queryset(request, applications, per_page=5)

    return render(request, 'applications/my_applications.html', {
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
    })
