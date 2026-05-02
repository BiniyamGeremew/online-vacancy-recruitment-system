"""
AI CV Parsing Service
Uses OpenAI GPT to extract structured information from CV text.
"""

import json
from openai import OpenAI
from django.conf import settings

# Initialize OpenAI client
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=settings.GITHUB_TOKEN
)


def parse_cv_with_ai(cv_text):
    """
    Parse CV text using AI to extract structured information.

    Args:
        cv_text (str): Plain text content of the CV

    Returns:
        dict: Structured CV data with keys:
            - skills: list of skills
            - education: list of education entries
            - field_of_study: primary field of study
            - years_of_experience: total years of experience
            - certifications: list of certifications
            - candidate_summary: brief summary of candidate

    Raises:
        ValueError: If AI parsing fails
    """

    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is empty")

    prompt = f"""
You are an expert HR assistant tasked with parsing a candidate's CV/resume text.
Extract the following structured information from the CV text provided below.

Return ONLY a valid JSON object with these exact keys:
- skills: array of technical and soft skills mentioned
- education: array of education entries (each with institution, degree, field, graduation_year if available)
- field_of_study: the primary academic field/discipline
- years_of_experience: estimated total years of professional experience (number)
- certifications: array of professional certifications mentioned
- candidate_summary: a 2-3 sentence summary of the candidate's background and qualifications

If information is not available, use empty arrays or appropriate defaults.

CV TEXT:
{cv_text[:4000]}
"""

    result_text = ''
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional CV parser. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()

        # Debug print - raw AI response
        print("\n===== RAW AI RESPONSE =====")
        print(result_text)
        print("===========================\n")

        # Clean markdown formatting if present
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]

        result_text = result_text.strip()

        # Parse JSON
        try:
            parsed_data = json.loads(result_text)
        except json.JSONDecodeError:
            parsed_data = json.loads(_extract_json_string(result_text))

        # Validate required keys
        required_keys = [
            'skills',
            'education',
            'field_of_study',
            'years_of_experience',
            'certifications',
            'candidate_summary'
        ]

        for key in required_keys:
            if key not in parsed_data:
                parsed_data[key] = [] if key in ['skills', 'education', 'certifications'] else ("" if key != 'years_of_experience' else 0)

        # Debug print - parsed AI data
        print("\n===== AI PARSED DATA =====")
        print(parsed_data)
        print("==========================\n")

        return parsed_data

    except json.JSONDecodeError:
        raise ValueError(f"AI returned invalid JSON: {result_text[:200]}")

    except Exception as e:
        raise ValueError(f"AI parsing failed: {str(e)}")


def _extract_json_string(text):
    """Extract the first JSON-like object from the AI response text."""
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or start > end:
        raise ValueError("Could not find JSON object in AI response")
    return text[start:end + 1]