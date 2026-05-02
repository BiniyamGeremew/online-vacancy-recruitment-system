from django.contrib import admin
from .models import Exam, Question, Choice, ExamSession, Answer, ExamResult, ExamSessionActivity


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ("exam", "question_text", "question_type", "marks")
    search_fields = ("question_text",)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title", "vacancy", "total_marks", "pass_mark", "duration_minutes", "is_published", "finalized", "created_at")
    list_filter = ("is_published", "finalized")
    inlines = [QuestionInline]


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = (
        "exam",
        "applicant",
        "start_time",
        "started_at",
        "end_time",
        "is_submitted",
        "tab_switch_count",
        "device_fingerprint",
        "user_agent",
    )
    search_fields = ("applicant__email", "exam__title")
    readonly_fields = ("security_flags", "activity_log")


@admin.register(ExamSessionActivity)
class ExamSessionActivityAdmin(admin.ModelAdmin):
    list_display = ("session", "activity_type", "timestamp")
    list_filter = ("activity_type",)
    search_fields = ("session__applicant__email", "session__exam__title")


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ("session", "total_score", "percentage", "passed", "evaluated_at")
    search_fields = ("session__applicant__email", "session__exam__title")
