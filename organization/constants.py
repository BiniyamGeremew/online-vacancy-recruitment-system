class RequestStatus:
    SUBMITTED = 'Submitted'
    APPROVED_BY_DEAN = 'Approved by Dean'
    REJECTED_BY_DEAN = 'Rejected by Dean'
    FORWARDED_TO_VP = 'Forwarded to VP'
    APPROVED_BY_VP = 'Approved by VP'
    REJECTED_BY_VP = 'Rejected by VP'
    FORWARDED_TO_HR = 'Forwarded to HR'
    VACANCY = 'Vacancy Announced'
    SCREENING = 'Screening'
    INTERVIEW = 'Interview'
    HIRED = 'Hiring Completed'

    CHOICES = [
        (SUBMITTED, 'Submitted'),
        (APPROVED_BY_DEAN, 'Approved by Dean'),
        (REJECTED_BY_DEAN, 'Rejected by Dean'),
        (FORWARDED_TO_VP, 'Forwarded to VP'),
        (APPROVED_BY_VP, 'Approved by VP'),
        (REJECTED_BY_VP, 'Rejected by VP'),
        (FORWARDED_TO_HR, 'Forwarded to HR'),
        (VACANCY, 'Vacancy Announced'),
        (SCREENING, 'Screening'),
        (INTERVIEW, 'Interview'),
        (HIRED, 'Hiring Completed'),
    ]