from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Notification


User = get_user_model()


def send_notification(user, title, message, link=None, notification_type=Notification.TYPE_APPLICATION_SUBMITTED):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        link=link or '',
        notification_type=notification_type,
    )


def send_email_notification(user, subject, message):
    if not user.email:
        return

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_submission_notifications(application):
    applicant_user = application.applicant.user
    position = application.position
    vacancy = position.vacancy

    applicant_title = 'Application Received'
    if application.status == application.STATUS_SUBMITTED:
        applicant_message = (
            f'Your application for {vacancy.employee_request.subject} ({position.academic_rank}) '
            f'has been received and is under review. Your current score is {application.ranking_score:.2f}.'
        )
    else:
        applicant_message = (
            f'Your application for {vacancy.employee_request.subject} ({position.academic_rank}) '
            'has been received. We will update you with the screening outcome shortly.'
        )

    send_notification(
        applicant_user,
        applicant_title,
        applicant_message,
        link='/applications/my-applications/',
        notification_type=Notification.TYPE_APPLICATION_SUBMITTED
    )
    send_email_notification(applicant_user, applicant_title, applicant_message)

    hr_title = 'New Application Submitted'
    hr_message = (
        f'A new application has been submitted for {vacancy.employee_request.subject} - {position.academic_rank} by '
        f'{applicant_user.get_full_name()} ({applicant_user.email}).'
    )

    hr_users = User.objects.filter(groups__name='hr_officer', is_active=True)
    for hr_user in hr_users:
        send_notification(
            hr_user,
            hr_title,
            hr_message,
            link=f'/hr_officer/vacancy/{vacancy.id}/screening/',
            notification_type=Notification.TYPE_APPLICATION_SUBMITTED
        )
        send_email_notification(hr_user, hr_title, hr_message)


def send_screening_update_notification(application):
    applicant_user = application.applicant.user
    vacancy = application.position.vacancy

    if application.status == application.STATUS_ELIGIBLE:
        title = 'Application Eligible'
        message = (
            f'Your application for {vacancy.employee_request.subject} is now eligible and ready for the next stage.'
        )
        notif_type = Notification.TYPE_ELIGIBLE
    elif application.status == application.STATUS_REJECTED:
        title = 'Application Rejected'
        message = (
            f'Your application for {vacancy.employee_request.subject} has been rejected.'
        )
        notif_type = Notification.TYPE_REJECTED
    elif application.status == application.STATUS_SHORTLISTED:
        title = 'Application Shortlisted'
        message = (
            f'Congratulations! Your application for {vacancy.employee_request.subject} has been shortlisted.'
        )
        notif_type = Notification.TYPE_SHORTLISTED
    else:
        return

    send_notification(
        applicant_user,
        title,
        message,
        link='/applications/my-applications/',
        notification_type=notif_type
    )
    send_email_notification(applicant_user, title, message)


def send_exam_scheduled_notification(application, exam):
    applicant_user = application.applicant.user
    vacancy = application.position.vacancy
    title = 'Exam Scheduled'
    message = (
        f'Your exam for {vacancy.employee_request.subject} has been scheduled. '
        f'Please begin it from your dashboard when ready.'
    )
    session = application.exam_sessions.filter(exam=exam).first()
    session_link = f'/applicant/exam/{session.id}/' if session else '/applicant/'

    send_notification(
        applicant_user,
        title,
        message,
        link=session_link,
        notification_type=Notification.TYPE_EXAM_SCHEDULED
    )
    send_email_notification(applicant_user, title, message)


def send_exam_started_notification(session):
    applicant_user = session.applicant
    title = 'Exam Started'
    message = (
        f'Your exam for {session.exam.title} has now started. Good luck!'
    )
    send_notification(
        applicant_user,
        title,
        message,
        link=f'/applicant/exam/{session.id}/',
        notification_type=Notification.TYPE_EXAM_STARTED
    )
    send_email_notification(applicant_user, title, message)


def send_exam_result_notification(session, result):
    applicant_user = session.applicant
    status_message = 'passed and moved to interview' if result.passed else 'failed and rejected'
    title = 'Exam Result Available'
    message = (
        f'Your exam result for {session.exam.title} is ready. '
        f'You scored {result.total_score:.2f}/{session.exam.total_marks} and have {status_message}.'
    )
    send_notification(
        applicant_user,
        title,
        message,
        link=f'/applicant/exam/{session.id}/result/',
        notification_type=Notification.TYPE_EXAM_RESULT
    )
    send_email_notification(applicant_user, title, message)


def send_hr_exam_completion_notification(exam, top_sessions):
    title = 'Exam Results Submitted to HR'
    message = (
        f'The exam "{exam.title}" results have been finalized and sent to HR. '
        f'{len(top_sessions)} candidates were moved to interview.'
    )
    hr_users = User.objects.filter(groups__name='hr_officer', is_active=True)
    for hr_user in hr_users:
        send_notification(
            hr_user,
            title,
            message,
            link=f'/hr_officer/vacancy/{exam.vacancy.id}/applications/',
            notification_type=Notification.TYPE_EXAM_COMPLETED
        )
        send_email_notification(hr_user, title, message)


def send_department_head_exam_summary(exam, passed_count, interview_count):
    if not exam.created_by:
        return
    title = 'Exam Summary Ready'
    message = (
        f'Exam "{exam.title}" has finished. {passed_count} applicants passed and {interview_count} were moved to interview.'
    )
    send_notification(
        exam.created_by,
        title,
        message,
        link=f'/department_head/vacancy/{exam.vacancy.id}/create_exam/',
        notification_type=Notification.TYPE_EXAM_COMPLETED
    )
    send_email_notification(exam.created_by, title, message)


def notify_matching_applicants_for_vacancy(vacancy):
    from applicant.models import ApplicantProfile

    field_tokens = set(
        token.strip().lower()
        for position in vacancy.positions.all()
        for token in (position.field_of_education or '').split()
        if token.strip()
    )

    if not field_tokens:
        return

    q_filter = Q()
    for token in field_tokens:
        q_filter |= Q(qualifications__qualification_type__icontains=token)
        q_filter |= Q(qualifications__department__icontains=token)

    matching_profiles = ApplicantProfile.objects.filter(q_filter).distinct().select_related('user')

    for profile in matching_profiles:
        user = profile.user
        title = 'New Vacancy Matches Your Profile'
        message = (
            f'A newly published vacancy for {vacancy.employee_request.subject} matches your field of study. '
            'Visit the vacancy board to apply now.'
        )
        send_notification(
            user,
            title,
            message,
            link='/applicant/vacancy_board_list/',
            notification_type=Notification.TYPE_VACANCY_MATCH
        )
        send_email_notification(user, title, message)
