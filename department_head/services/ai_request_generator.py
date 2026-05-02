from openai import OpenAI
from django.conf import settings

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=settings.GITHUB_TOKEN
)


def build_positions_text(positions):
    """
    Convert position list into structured text for the AI prompt.
    """
    text = ""

    for pos in positions:
        text += f"""
Academic Qualification: {pos.get('academic_qualification', '')}
Academic Rank: {pos.get('academic_rank', '')}
Field of Study: {pos.get('study_department', '')}
Required Experience: {pos.get('experience_years', 0)} years
Number of Positions: {pos.get('number_of_employees', 1)}
Minimum CGPA: {pos.get('cgpa_requirement', '')}
"""

    return text.strip()


def generate_employee_request(request_data):
    """
    Generate a clear and professional employee recruitment request
    based strictly on structured form data.
    """

    department = request_data.get('department', '')
    subject = request_data.get('subject', '')
    positions = request_data.get('positions', [])

    positions_text = build_positions_text(positions)

    structured_data = f"""
Department: {department}
Request Subject: {subject}

Position Requirements:
{positions_text}
"""

    prompt = f"""
You are an academic HR assistant responsible for drafting formal recruitment requests for a university.

Transform the structured data into a clear and professional HR request document.

STRICT RULES:
- Use ONLY the information provided.
- Do NOT invent explanations, motivations, or institutional justifications.
- Do NOT add phrases such as "critical need", "growing demand", or similar assumptions.
- Do NOT include greetings, signatures, or letter formatting.
- Keep the language formal, neutral, and concise.
- Do not introduce responsibilities or duties that are not provided.

WRITING GUIDELINES:
- Start with a clear title based on the request subject.
- State that the department "seeks to hire".
- Refer to positions using proper academic phrasing such as "Lecturers in Computer Maintenance".
- Clearly mention:
  - academic qualification
  - academic rank
  - field of study
  - experience requirement
  - CGPA requirement (if provided)
- Maintain a natural but structured paragraph format suitable for an internal HR document.

EMPLOYEE REQUEST DATA:
{structured_data}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error generating request: {str(e)}"