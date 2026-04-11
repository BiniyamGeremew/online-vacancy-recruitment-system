from django.conf import settings
from django.db import models

from organization.models import TimeStampedModel


class ApplicantProfile(TimeStampedModel):
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'

    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
    ]

    MARITAL_SINGLE = 'single'
    MARITAL_MARRIED = 'married'
    MARITAL_DIVORCED = 'divorced'
    MARITAL_WIDOWED = 'widowed'

    MARITAL_STATUS_CHOICES = [
        (MARITAL_SINGLE, 'Single'),
        (MARITAL_MARRIED, 'Married'),
        (MARITAL_DIVORCED, 'Divorced'),
        (MARITAL_WIDOWED, 'Widowed'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applicant_profile'
    )
    mobile_number = models.CharField(max_length=20, blank=True)
    father_name = models.CharField(max_length=64, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        blank=True
    )
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True
    )
    title = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    zone = models.CharField(max_length=100, blank=True)
    wereda = models.CharField(max_length=100, blank=True)
    kebele = models.CharField(max_length=100, blank=True)
    house_number = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Applicant Profile'
        verbose_name_plural = 'Applicant Profiles'

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def has_step1(self):
        required_fields = [
            self.user.email,
            self.user.first_name,
            self.user.last_name,
            self.mobile_number,
            self.father_name,
            self.birth_date,
            self.marital_status,
            self.gender,
            self.title,
            self.country,
            self.region,
            self.zone,
            self.wereda,
            self.kebele,
            self.house_number,
            self.postal_code,
        ]
        return all(required_fields)

    def has_step2(self):
        uploaded_types = self.documents.values_list('document_type', flat=True)
        return {
            ApplicantDocument.DOCUMENT_RESUME,
            ApplicantDocument.DOCUMENT_GRADE_8,
        }.issubset(set(uploaded_types))

    def has_step3(self):
        return self.qualifications.exists()

    def has_step4(self):
        return self.employments.exists()

    def profile_is_complete(self):
        return self.has_step1() and self.has_step2() and self.has_step3() and self.has_step4()


class ApplicantDocument(TimeStampedModel):
    DOCUMENT_RESUME = 'resume'
    DOCUMENT_GRADE_8 = 'grade8'

    DOCUMENT_TYPE_CHOICES = [
        (DOCUMENT_RESUME, 'Resume (CV)'),
        (DOCUMENT_GRADE_8, 'Grade 8 Certificate'),
    ]

    applicant = models.ForeignKey(
        ApplicantProfile,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES
    )
    file = models.FileField(upload_to='applicant/documents/')

    class Meta:
        unique_together = ('applicant', 'document_type')
        verbose_name = 'Applicant Document'
        verbose_name_plural = 'Applicant Documents'

    def __str__(self):
        return f"{self.applicant.user.username} - {self.get_document_type_display()}"


class EducationQualification(TimeStampedModel):

    BACHELOR = "bachelor"
    POST_GRADUATE = "post_graduate"
    DOCTORATE = "doctorate"

    CATEGORY_CHOICES = [
        (BACHELOR, "Bachelor Degree"),
        (POST_GRADUATE, "Post Graduate Education"),
        (DOCTORATE, "Doctorate"),
    ]

    profile = models.ForeignKey(
        ApplicantProfile,
        on_delete=models.CASCADE,
        related_name='qualifications'
    )

    institution_name = models.CharField(max_length=255)

    qualification_category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    qualification_type = models.CharField(max_length=255)

    department = models.CharField(max_length=255)

    grade = models.DecimalField(max_digits=4, decimal_places=2)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    diploma_certificate = models.FileField(
        upload_to='applicant/qualifications/',
        null=True,
        blank=True
    )

    transcript = models.FileField(
        upload_to='applicant/qualifications/',
        null=True,
        blank=True
    )

    cost_sharing_document = models.FileField(
        upload_to='applicant/qualifications/',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-end_date']

    def __str__(self):
        return f"{self.institution_name} - {self.qualification_type}"


class EmploymentHistory(TimeStampedModel):
    profile = models.ForeignKey(
        ApplicantProfile,
        on_delete=models.CASCADE,
        related_name='employments'
    )
    job_category = models.CharField(max_length=255)
    employer = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    experience_letter = models.FileField(
        upload_to='applicant/experiences/',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Employment History'
        verbose_name_plural = 'Employment Histories'

    def __str__(self):
        return f"{self.employer} - {self.job_title}"
