import json
import random
import re
from decimal import Decimal
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from core.utils.pagination import paginate_queryset
from django.views.decorators.http import require_POST

from hr_officer.models import Vacancy
from applications.models import Application
from .models import Exam, Question, Choice, ExamSession, Answer, ExamResult, ExamSessionActivity
from .forms import ExamCreateForm, ManualQuestionForm, QuestionUploadForm
from .services import generate_exam_questions
from notifications.services import (
    send_exam_scheduled_notification,
    send_exam_started_notification,
    send_exam_result_notification,
    send_hr_exam_completion_notification,
    send_department_head_exam_summary,
)


def user_can_manage_vacancy(user, vacancy: Vacancy) -> bool:
    profile = getattr(user, 'userprofile', None)
    if profile and profile.department:
        return profile.department == vacancy.employee_request.department
    return False


def create_question_from_data(exam: Exam, question_data: dict, order: int) -> Question:
    question_type = question_data.get('question_type', Question.TYPE_MCQ)
    question = Question.objects.create(
        exam=exam,
        question_text=question_data.get('question_text') or question_data.get('text', ''),
        question_type=question_type,
        marks=question_data.get('marks', 1) or 1,
        order=order,
    )

    if question.question_type == Question.TYPE_MCQ:
        choices = question_data.get('choices', [])
        correct_answer = question_data.get('correct_answer', '').strip()
        for option in choices:
            Choice.objects.create(
                question=question,
                option_text=option.strip(),
                is_correct=option.strip() == correct_answer,
            )

    return question


def build_question_payload_from_upload(file_data):
    try:
        content = json.load(file_data)
    except Exception:
        return []

    questions = content.get('questions') if isinstance(content, dict) else []
    if not isinstance(questions, list):
        return []

    payload = []
    for item in questions:
        payload.append({
            'question_text': item.get('question_text') or item.get('text', ''),
            'question_type': item.get('question_type', Question.TYPE_MCQ),
            'marks': item.get('marks', 1),
            'choices': item.get('choices', []),
            'correct_answer': item.get('correct_answer', ''),
        })
    return payload


def log_exam_activity(session: ExamSession, activity_type: str, details: dict = None):
    details = details or {}
    ExamSessionActivity.objects.create(
        session=session,
        activity_type=activity_type,
        details=details,
    )
    session.activity_log.setdefault('events', []).append({
        'type': activity_type,
        'details': details,
        'time': timezone.now().isoformat(),
    })
    session.save(update_fields=['activity_log'])


def get_exam_threshold(exam: Exam) -> tuple[Decimal, Decimal]:
    question_sum = exam.questions.aggregate(total=models.Sum('marks'))['total'] or 0
    total_marks = Decimal(exam.total_marks or question_sum or 0)
    if exam.pass_mark:
        pass_mark = Decimal(exam.pass_mark)
    else:
        pass_mark = (total_marks * Decimal('0.5')).quantize(Decimal('0'), rounding='ROUND_HALF_UP') if total_marks else Decimal('0')
    return total_marks, pass_mark


def finalize_exam_statuses(exam: Exam):
    passed_sessions = list(ExamSession.objects.filter(
        exam=exam,
        is_submitted=True,
        result__passed=True
    ).order_by('-result__total_score'))
    top_sessions = passed_sessions[:4]
    other_passed = passed_sessions[4:]

    for top_session in top_sessions:
        application = top_session.application
        if application.status != Application.STATUS_INTERVIEW:
            application.status = Application.STATUS_INTERVIEW
            application.save()

    for other_session in other_passed:
        application = other_session.application
        if application.status != Application.STATUS_REJECTED:
            application.status = Application.STATUS_REJECTED
            application.save()

    return top_sessions


def assign_exam_to_shortlisted_applicants(exam: Exam) -> int:
    applications = Application.objects.filter(
        position__vacancy=exam.vacancy,
        status=Application.STATUS_SHORTLISTED
    ).select_related('applicant__user')

    assigned_count = 0
    for application in applications:
        application.status = Application.STATUS_EXAM
        application.save()

        session, created = ExamSession.objects.get_or_create(
            exam=exam,
            application=application,
            defaults={
                'applicant': application.applicant.user,
                'ip_address': '',
            }
        )
        if created:
            assigned_count += 1

        send_exam_scheduled_notification(application, exam)

    return assigned_count


def ensure_session_order(session: ExamSession):
    if not session.question_order:
        question_ids = list(session.exam.questions.values_list('id', flat=True))
        random.shuffle(question_ids)
        session.question_order = question_ids

    order_by_question = {}
    for question_id in session.question_order:
        order_by_question[str(question_id)] = []

    if not session.choice_order:
        for question in session.exam.questions.all():
            choice_ids = list(question.choices.values_list('id', flat=True))
            random.shuffle(choice_ids)
            session.choice_order[str(question.id)] = choice_ids

    session.save()
    return session


def get_ordered_questions(session: ExamSession):
    question_ids = session.question_order or []
    questions = list(session.exam.questions.filter(id__in=question_ids))
    lookup = {q.id: q for q in questions}
    ordered = [lookup[qid] for qid in question_ids if qid in lookup]
    if not ordered:
        ordered = list(session.exam.questions.all())
    return ordered


def get_ordered_choices(session: ExamSession, question: Question):
    order = session.choice_order.get(str(question.id), [])
    choices = list(question.choices.all())
    choice_lookup = {c.id: c for c in choices}
    ordered = [choice_lookup[cid] for cid in order if cid in choice_lookup]
    if len(ordered) != len(choices):
        remaining = [c for c in choices if c.id not in order]
        random.shuffle(remaining)
        ordered.extend(remaining)
    return ordered


def score_short_answer(question: Question, text_answer: str) -> Decimal:
    if not text_answer:
        return Decimal('0')

    normalized = text_answer.lower()
    tokens = set(re.findall(r"\w{4,}", question.question_text.lower()))
    if not tokens:
        return Decimal(question.marks)

    matched = sum(1 for token in tokens if token in normalized)
    ratio = min(Decimal(matched) / Decimal(len(tokens)), Decimal('1'))
    return (Decimal(question.marks) * ratio).quantize(Decimal('0.01'))


@login_required
def create_exam(request, vacancy_id):
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)
    if not user_can_manage_vacancy(request.user, vacancy):
        return HttpResponseForbidden()

    exam = Exam.objects.filter(vacancy=vacancy).first()
    exam_form = ExamCreateForm(request.POST or None, instance=exam)
    manual_form = ManualQuestionForm(request.POST or None)

    deadline_passed = vacancy.deadline and vacancy.deadline <= timezone.now().date()
    can_prepare_exam = bool(deadline_passed and vacancy.shortlist_finalized)

    if request.method == 'POST' and can_prepare_exam:
        action = request.POST.get('action')

        if action == 'save_exam' and exam_form.is_valid():
            exam = exam_form.save(commit=False)
            exam.vacancy = vacancy
            exam.created_by = request.user
            exam.is_published = False
            exam.save()
            messages.success(request, 'Exam settings saved.')
            return redirect('department_head:create_exam', vacancy_id=vacancy.id)

        elif action == 'generate_ai' and exam:
            from .services.ai_question_service import AIQuestionService
            service = AIQuestionService()
            try:
                total_questions = int(request.POST.get('question_count', 10))
            except (TypeError, ValueError):
                total_questions = 10
            difficulty = request.POST.get('difficulty_level', 'medium') or 'medium'
            try:
                mcq_count = int(request.POST.get('mcq_count', 0))
            except (TypeError, ValueError):
                mcq_count = 0
            try:
                short_answer_count = int(request.POST.get('short_answer_count', 0))
            except (TypeError, ValueError):
                short_answer_count = 0

            questions_data = service.generate_questions_for_exam(
                exam,
                total_questions=total_questions,
                difficulty=difficulty,
                mcq_count=mcq_count,
                short_answer_count=short_answer_count,
            )

            if not questions_data:
                messages.error(request, 'AI did not return any valid questions. Please try again or adjust the exam settings.')
                return redirect('department_head:create_exam', vacancy_id=vacancy.id)

            service.store_questions_in_session(request, exam.id, questions_data)
            return redirect('department_head:ai_review', exam_id=exam.id)

        elif action == 'add_question' and exam and manual_form.is_valid():
            from .services.manual_question_service import ManualQuestionService
            service = ManualQuestionService()
            question_data = manual_form.cleaned_data
            if question_data['question_type'] == Question.TYPE_MCQ:
                question_data['choices'] = [
                    question_data['choice_1'],
                    question_data['choice_2'],
                    question_data['choice_3'],
                    question_data['choice_4'],
                ]
                question_data['correct_choice'] = question_data[f"choice_{question_data['correct_choice']}"]
            service.add_question_to_exam(exam, question_data)
            messages.success(request, 'Question added successfully.')
            return redirect('department_head:create_exam', vacancy_id=vacancy.id)

        elif action == 'publish_exam' and exam:
            from .services.manual_question_service import ManualQuestionService
            service = ManualQuestionService()
            if service.can_publish_exam(exam):
                exam.is_published = True
                exam.save()
                # Publish questions
                exam.questions.filter(status=Question.STATUS_DRAFT).update(status=Question.STATUS_PUBLISHED)
                assigned = assign_exam_to_shortlisted_applicants(exam)
                messages.success(request, f'Exam published and assigned to {assigned} applicants.')
            else:
                messages.error(request, 'Cannot publish exam without questions.')
            return redirect('department_head:create_exam', vacancy_id=vacancy.id)

    draft_questions = []
    draft_question_count = 0
    published_question_count = 0
    has_draft_questions = False
    if exam:
        from .services.manual_question_service import ManualQuestionService
        service = ManualQuestionService()
        draft_questions = service.get_draft_questions(exam)
        draft_question_count = len(draft_questions)
        published_question_count = exam.questions.filter(status=Question.STATUS_PUBLISHED).count()
        has_draft_questions = draft_question_count > 0

    return render(request, 'examinations/exam_create.html', {
        'vacancy': vacancy,
        'exam': exam,
        'exam_form': exam_form,
        'manual_form': manual_form,
        'draft_questions': draft_questions,
        'draft_question_count': draft_question_count,
        'published_question_count': published_question_count,
        'has_draft_questions': has_draft_questions,
        'can_prepare_exam': can_prepare_exam,
    })


@login_required
def ai_review_questions(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not user_can_manage_vacancy(request.user, exam.vacancy):
        return HttpResponseForbidden()

    from .services.ai_question_service import AIQuestionService
    service = AIQuestionService()
    questions_data = service.get_questions_from_session(request, exam.id)

    if not questions_data:
        messages.error(request, 'No questions to review. Please generate questions first.')
        return redirect('department_head:create_exam', vacancy_id=exam.vacancy.id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_draft':
            service.save_questions_to_draft(exam, questions_data)
            service.clear_session_questions(request, exam.id)
            messages.success(request, f'Saved {len(questions_data)} questions as draft.')
            return redirect('department_head:create_exam', vacancy_id=exam.vacancy.id)

        elif action == 'regenerate':
            # Clear session and redirect back to generate
            service.clear_session_questions(request, exam.id)
            return redirect('department_head:create_exam', vacancy_id=exam.vacancy.id)

    return render(request, 'examinations/ai_review.html', {
        'exam': exam,
        'questions_data': questions_data,
    })


@login_required
def exam_sessions(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not user_can_manage_vacancy(request.user, exam.vacancy):
        return HttpResponseForbidden()

    sessions = exam.sessions.select_related('applicant', 'application').order_by('-start_time')
    pagination = paginate_queryset(request, sessions, per_page=5)

    return render(request, 'examinations/exam_sessions.html', {
        'exam': exam,
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
    })


@login_required
def department_head_exam_results(request, vacancy_id):
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)
    if not user_can_manage_vacancy(request.user, vacancy):
        return HttpResponseForbidden()

    exam = vacancy.exams.filter(is_published=True).order_by('-created_at').first()
    sessions = exam.sessions.select_related('applicant', 'application', 'result').order_by('-start_time') if exam else []
    pagination = paginate_queryset(request, sessions, per_page=5)
    page_obj = pagination['page_obj']

    if request.method == 'POST' and request.POST.get('action') == 'send_results' and exam:
        top_sessions = finalize_exam_statuses(exam)
        exam.finalized = True
        exam.finalized_at = timezone.now()
        exam.save(update_fields=['finalized', 'finalized_at'])
        send_hr_exam_completion_notification(exam, top_sessions)
        messages.success(request, 'Exam results have been sent to HR Officer.')
        return redirect('department_head:exam_results', vacancy_id=vacancy.id)

    return render(request, 'examinations/exam_results_list.html', {
        'vacancy': vacancy,
        'exam': exam,
        'page_obj': page_obj,
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
        'view_mode': 'department_head',
    })


@login_required
def hr_officer_exam_results(request, vacancy_id):
    if not request.user.groups.filter(name='hr_officer').exists():
        return HttpResponseForbidden()

    vacancy = get_object_or_404(Vacancy, id=vacancy_id)
    exam = vacancy.exams.filter(is_published=True).order_by('-created_at').first()
    sessions = exam.sessions.select_related('applicant', 'application', 'result').order_by('-start_time') if exam else []
    pagination = paginate_queryset(request, sessions, per_page=5)

    return render(request, 'examinations/exam_results_list.html', {
        'vacancy': vacancy,
        'exam': exam,
        'page_obj': pagination['page_obj'],
        'paginator': pagination['paginator'],
        'pagination_query': pagination['pagination_query'],
        'view_mode': 'hr_officer',
    })


@login_required
def take_exam(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id, applicant=request.user)
    exam = session.exam
    if not exam.is_published:
        return HttpResponseForbidden()

    if session.is_submitted:
        return redirect('applicant:exam_result', session_id=session.id)

    if request.method == 'POST':
        action = request.POST.get('action')
        fingerprint = request.POST.get('device_fingerprint', '')

        if session.device_fingerprint and fingerprint and session.device_fingerprint != fingerprint:
            return HttpResponseForbidden('Exam session blocked for a different device.')

        if action == 'submit_exam':
            if not session.start_time:
                return HttpResponseForbidden('Exam has not been started.')

            if session.is_expired():
                messages.warning(request, 'This exam session has expired. Your current answers will be processed.')
                log_exam_activity(session, 'time_expired', {
                    'current_time': timezone.now().isoformat(),
                })

            total_score = Decimal('0')
            Answer.objects.filter(session=session).delete()

            for question in get_ordered_questions(session):
                field_name = f'question_{question.id}'
                if question.question_type == Question.TYPE_MCQ:
                    selected_choice_id = request.POST.get(field_name)
                    answer = Answer(session=session, question=question)
                    if selected_choice_id:
                        try:
                            choice = Choice.objects.get(id=int(selected_choice_id), question=question)
                            answer.selected_choice = choice
                            answer.score_awarded = Decimal(question.marks) if choice.is_correct else Decimal('0')
                        except Choice.DoesNotExist:
                            answer.score_awarded = Decimal('0')
                    else:
                        answer.score_awarded = Decimal('0')
                    answer.save()
                    total_score += answer.score_awarded
                else:
                    text_answer = request.POST.get(field_name, '').strip()
                    answer = Answer(
                        session=session,
                        question=question,
                        text_answer=text_answer,
                        score_awarded=score_short_answer(question, text_answer),
                    )
                    answer.save()
                    total_score += answer.score_awarded

            total_marks, pass_mark = get_exam_threshold(exam)
            session.end_time = timezone.now()
            session.is_submitted = True
            session.save()
            log_exam_activity(session, 'exam_submitted', {
                'total_score': str(total_score),
                'total_marks': str(total_marks),
                'pass_mark': str(pass_mark),
            })

            percentage = (total_score / total_marks * Decimal('100')).quantize(Decimal('0.01')) if total_marks else Decimal('0')
            passed = total_score >= pass_mark

            result = ExamResult.objects.create(
                session=session,
                total_score=total_score,
                percentage=percentage,
                passed=passed,
            )

            application = session.application
            application.status = Application.STATUS_INTERVIEW if passed else Application.STATUS_REJECTED
            application.save()

            send_exam_result_notification(session, result)

            submitted_count = exam.sessions.filter(is_submitted=True).count()
            total_sessions = exam.sessions.count()

            if total_sessions > 0 and submitted_count == total_sessions:
                top_sessions = finalize_exam_statuses(exam)
                if not exam.finalized:
                    exam.finalized = True
                    exam.finalized_at = timezone.now()
                    exam.save(update_fields=['finalized', 'finalized_at'])
                send_hr_exam_completion_notification(exam, top_sessions)
                send_department_head_exam_summary(
                    exam,
                    exam.sessions.filter(is_submitted=True, result__passed=True).count(),
                    len(top_sessions)
                )

            return redirect('applicant:exam_result', session_id=session.id)

    show_started = bool(session.start_time)
    remaining_seconds = None
    questions = []
    if show_started:
        ensure_session_order(session)
        end_time = session.start_time + timedelta(minutes=exam.duration_minutes)
        remaining = (end_time - timezone.now()).total_seconds()
        remaining_seconds = max(int(remaining), 0)

        for question in get_ordered_questions(session):
            choices = get_ordered_choices(session, question) if question.question_type == Question.TYPE_MCQ else []
            questions.append({
                'question': question,
                'choices': choices,
            })

    return render(request, 'examinations/exam_take.html', {
        'session': session,
        'exam': exam,
        'show_started': show_started,
        'remaining_seconds': remaining_seconds,
        'questions': questions,
    })


@login_required
@require_POST
def exam_security_event(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id, applicant=request.user)
    event_type = request.POST.get('event_type')
    fingerprint = request.POST.get('device_fingerprint', '')

    if not fingerprint:
        return JsonResponse({'error': 'Missing fingerprint'}, status=400)

    if session.device_fingerprint and fingerprint != session.device_fingerprint:
        return JsonResponse({'error': 'Session blocked for a different device.'}, status=403)

    if event_type == 'start':
        if session.is_submitted:
            return JsonResponse({'error': 'This exam session has already been submitted.'}, status=403)

        if session.start_time and fingerprint != session.device_fingerprint:
            return JsonResponse({'error': 'Exam already active on another device.'}, status=403)

        if not session.start_time:
            session.start_time = timezone.now()
            session.started_at = timezone.now()
            session.device_fingerprint = fingerprint
            session.user_agent = request.META.get('HTTP_USER_AGENT', '')
            session.ip_address = request.META.get('REMOTE_ADDR', '')
            ensure_session_order(session)
            session.save()
            log_exam_activity(session, 'exam_started', {
                'user_agent': session.user_agent,
                'ip_address': session.ip_address,
            })
            send_exam_started_notification(session)
        return JsonResponse({'status': 'started'})

    if event_type == 'tab_switch':
        session.tab_switch_count += 1
        session.security_flags['tab_switch_count'] = session.tab_switch_count
        log_exam_activity(session, 'tab_switch', {
            'tab_switch_count': session.tab_switch_count,
        })
        return JsonResponse({'status': 'recorded', 'tab_switch_count': session.tab_switch_count})

    if event_type == 'reload_attempt':
        log_exam_activity(session, 'reload_attempt', {
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR', ''),
        })
        session.security_flags.setdefault('reload_attempts', 0)
        session.security_flags['reload_attempts'] += 1
        session.save(update_fields=['security_flags'])
        return JsonResponse({'status': 'reload recorded'})

    return JsonResponse({'error': 'Invalid event type'}, status=400)


@login_required
def exam_result(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id, applicant=request.user)
    if not session.is_submitted or not hasattr(session, 'result'):
        return redirect('applicant:take_exam', session_id=session.id)

    next_step = 'Your application is under review for interview.' if session.result.passed else 'Your application was rejected. Please check your notifications for details.'
    if session.result.passed and session.application.status == Application.STATUS_INTERVIEW:
        next_step = 'Congratulations! You have been moved to interview stage.'

    return render(request, 'examinations/exam_result.html', {
        'session': session,
        'result': session.result,
        'next_step': next_step,
    })
