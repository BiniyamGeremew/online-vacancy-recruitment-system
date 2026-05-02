from openai import OpenAI
from django.conf import settings

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=settings.GITHUB_TOKEN
)


def build_positions_text(employee_request):
    text = ""

    for item in employee_request.items.all():
        text += f"""
Academic Rank: {item.academic_rank}
Minimum CGPA: {item.cgpa_requirement}
Number of Positions: {item.number_of_employees}
"""

    return text.strip()


def generate_vacancy_text(
    employee_request,
    vacancy_type,
    experience,
    skills,
    salary,
    announcement_date=None,
    deadline=None
):
    university = "Haramaya University"
    department = employee_request.department.name
    subject = employee_request.subject
    narrative = employee_request.request_narrative

    positions_text = build_positions_text(employee_request)

    def format_date(value):
        if not value:
            return "To be announced"
        return value.strftime("%B %d, %Y")

    announcement_date = format_date(announcement_date)
    deadline = format_date(deadline)

    structured_data = f"""
University: {university}
Department: {department}
Vacancy Title: {subject}

Request Narrative:
{narrative}

Vacancy Type:
{vacancy_type}

Experience Requirement:
{experience}

Skills:
{skills}

Available Positions:
{positions_text}

Salary Information:
{salary}

Announcement Date:
{announcement_date}

Application Deadline:
{deadline}
"""

    prompt = f"""
You are an HR officer writing a REAL-WORLD UNIVERSITY JOB VACANCY ANNOUNCEMENT.

STYLE:
- Modern job advertisement format (not academic report)
- Clean headings
- Professional and natural tone
- Must look like a real published vacancy
- Output must be plain text only

STRUCTURE:

ORGANIZATION + VACANCY TYPE

JOB POSITION

Required Qualification and Experience
- Education
- Experience
- Additional requirements

Key Responsibilities
- Bullet points

Required Skills
- Bullet points

Location
Deadline

How to Apply

RULES:
- DO NOT use Markdown formatting
- DO NOT use **bold**, *, or #
- Use plain text headings only
- DO NOT use placeholders like [insert date]
- DO NOT invent information
- If missing data exists, use "To be announced"
- Use ONLY provided data

DATA:
{structured_data}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    return response.choices[0].message.content.strip()