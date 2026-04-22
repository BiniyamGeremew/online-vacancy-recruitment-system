# hr_officer/constants.py



class VacancyStatus:
    DRAFT = 'draft'
    PUBLISHED = 'published'
    CLOSED = 'closed'

    CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (CLOSED, 'Closed'),
    ]


class ApplicationStatus:
    SCREENING = 'screening'
    INTERVIEW = 'interview'
    HIRED = 'hired'
    REJECTED = 'rejected'

    CHOICES = [
        (SCREENING, 'Screening'),
        (INTERVIEW, 'Interview'),
        (HIRED, 'Hired'),
        (REJECTED, 'Rejected'),
    ]