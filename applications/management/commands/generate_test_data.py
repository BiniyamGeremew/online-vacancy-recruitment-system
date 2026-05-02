from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from applicant.models import ApplicantProfile, EducationQualification, EmploymentHistory, ApplicantDocument
from hr_officer.models import Vacancy, VacancyPosition
from applications.models import Application
import random

class Command(BaseCommand):
    help = 'Generate test applicants and applications for system testing'

    def handle(self, *args, **options):
        # Test data
        names = [
            ('Abel', 'Tesfaye'),
            ('Hana', 'Alemu'),
            ('Dawit', 'Girma'),
            ('Selamawit', 'Kebede'),
            ('Nahom', 'Desta'),
            ('Liya', 'Abebe'),
            ('Bereket', 'Haile'),
            ('Ruth', 'Yohannes'),
            ('Samuel', 'Bekele'),
            ('Meklit', 'Tadesse'),
        ]

        universities = [
            'Addis Ababa University',
            'Bahir Dar University',
            'Jimma University',
            'Hawassa University',
            'Mekelle University',
            'Adama Science and Technology University',
        ]

        fields_of_study = [
            'Computer Science',
            'Information Technology',
            'Software Engineering',
            'Electrical Engineering',
            'Mechanical Engineering',
            'Civil Engineering',
        ]

        # Get existing documents to reuse
        existing_docs = ApplicantDocument.objects.all()
        if not existing_docs.exists():
            self.stdout.write(self.style.ERROR('No existing documents found. Please create at least one applicant with documents first.'))
            return

        cv_doc = existing_docs.filter(document_type='resume').first()
        transcript_doc = existing_docs.filter(document_type='grade8').first()

        if not cv_doc or not transcript_doc:
            self.stdout.write(self.style.ERROR('Missing CV or transcript documents.'))
            return

        # Get available vacancies
        vacancies = Vacancy.objects.filter(status='published')
        if not vacancies.exists():
            self.stdout.write(self.style.ERROR('No published vacancies found.'))
            return

        for i, (first_name, last_name) in enumerate(names, 1):
            email = f'applicant{i}@gmail.com'
            password = 'ww90wet873452'

            # Create user
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'Created user: {email}')
            else:
                self.stdout.write(f'User {email} already exists, skipping.')

            # Create profile
            profile, created = ApplicantProfile.objects.get_or_create(
                user=user,
                defaults={
                    'mobile_number': f'091{random.randint(10000000, 99999999)}',
                    'father_name': f'Father of {first_name}',
                    'birth_date': timezone.now().date().replace(year=timezone.now().year - random.randint(22, 30)),
                    'marital_status': random.choice(['single', 'married']),
                    'gender': random.choice(['male', 'female']),
                    'title': 'Mr.' if user.first_name else 'Ms.',
                    'country': 'Ethiopia',
                    'region': 'Addis Ababa',
                    'zone': 'Bole',
                    'wereda': '01',
                    'kebele': '01',
                    'house_number': f'{random.randint(1, 999)}',
                    'postal_code': '1000',
                }
            )

            # Create education
            cgpa = round(random.uniform(2.3, 3.9), 2)
            grad_year = timezone.now().year - random.randint(1, 5)
            EducationQualification.objects.get_or_create(
                profile=profile,
                institution_name=random.choice(universities),
                qualification_category='bachelor',
                qualification_type=random.choice(fields_of_study),
                department=random.choice(fields_of_study),
                grade=cgpa,
                start_date=timezone.now().date().replace(year=grad_year-4),
                end_date=timezone.now().date().replace(year=grad_year),
            )

            # Create employment
            EmploymentHistory.objects.get_or_create(
                profile=profile,
                job_category='IT',
                employer=f'Company {i}',
                job_title='Software Developer',
                start_date=timezone.now().date().replace(year=grad_year),
                end_date=None,
                experience_letter=None,
            )

            # Create documents (reuse existing)
            ApplicantDocument.objects.get_or_create(
                applicant=profile,
                document_type='resume',
                defaults={'file': cv_doc.file}
            )
            ApplicantDocument.objects.get_or_create(
                applicant=profile,
                document_type='grade8',
                defaults={'file': transcript_doc.file}
            )

            # Create applications for random vacancies
            for vacancy in random.sample(list(vacancies), min(2, len(vacancies))):
                positions = list(vacancy.positions.all())
                if positions:
                    position = random.choice(positions)
                    Application.objects.get_or_create(
                        applicant=profile,
                        position=position,
                        defaults={
                            'status': 'submitted',
                            'cover_letter': f'Cover letter for {position.academic_rank}',
                        }
                    )

        self.stdout.write(self.style.SUCCESS('Test data generation completed.'))