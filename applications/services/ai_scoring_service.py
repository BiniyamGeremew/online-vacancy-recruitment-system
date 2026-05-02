"""
AI Candidate Evaluation Service
Uses OpenAI GPT to evaluate candidate fit for a position based on requirements and CV data.
"""

import json
from openai import OpenAI
from django.conf import settings

# Initialize OpenAI client
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=settings.GITHUB_TOKEN
)


def evaluate_candidate_with_ai(vacancy_info, parsed_cv_data):
    """
    Evaluate candidate fit using AI analysis.

    Args:
        vacancy_info (dict): Job vacancy information with keys:
            - title: job title
            - description: job description
            - required_skills: required skills text
            - field_of_study: required field of study
            - minimum_cgpa: minimum CGPA requirement
        parsed_cv_data (dict): Parsed CV data from ai_parser

    Returns:
        tuple: (candidate_score, candidate_summary)
            - candidate_score: float between 0-100
            - candidate_summary: str AI-generated summary

    Raises:
        ValueError: If AI evaluation fails
    """
    prompt = f"""
You are an expert HR recruiter evaluating a candidate for a job position.

JOB POSITION DETAILS:
Title: {vacancy_info.get('title', 'N/A')}
Description: {vacancy_info.get('description', 'N/A')}
Required Skills: {vacancy_info.get('required_skills', 'N/A')}
Required Field of Study: {vacancy_info.get('field_of_study', 'N/A')}
Minimum CGPA: {vacancy_info.get('minimum_cgpa', 'N/A')}

CANDIDATE INFORMATION:
Skills: {', '.join(parsed_cv_data.get('skills', []))}
Education: {json.dumps(parsed_cv_data.get('education', []), indent=2)}
Field of Study: {parsed_cv_data.get('field_of_study', 'N/A')}
Years of Experience: {parsed_cv_data.get('years_of_experience', 0)}
Certifications: {', '.join(parsed_cv_data.get('certifications', []))}
Candidate Summary: {parsed_cv_data.get('candidate_summary', 'N/A')}

Please evaluate this candidate's fit for the position on a scale of 0-100, where:
- 0-20: Poor fit, missing most requirements
- 21-40: Below average fit, some relevant experience but significant gaps
- 41-60: Average fit, meets basic requirements
- 61-80: Good fit, strong match with some expertise
- 81-100: Excellent fit, highly qualified with extensive relevant experience

Consider:
1. Relevance of skills to job requirements
2. Educational background match
3. Years of experience appropriateness
4. Overall qualifications alignment

Return ONLY a valid JSON object with these exact keys:
- candidate_score: number between 0-100
- candidate_summary: 2-3 sentence evaluation explaining the score and highlighting strengths/weaknesses
"""

    result_text = ''
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional HR evaluator. Always return valid JSON with candidate_score and candidate_summary."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Low-medium temperature for consistent evaluation
            max_tokens=500
        )

        result_text = response.choices[0].message.content.strip()
        print("AI EVALUATION RAW RESPONSE:", result_text)

        # Clean up response
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]

        result_text = result_text.strip()

        # Parse JSON
        try:
            evaluation = json.loads(result_text)
        except json.JSONDecodeError:
            evaluation = json.loads(_extract_json_string(result_text))

        # Validate response
        if 'candidate_score' not in evaluation or 'candidate_summary' not in evaluation:
            raise ValueError("AI response missing required fields")

        score = float(evaluation['candidate_score'])
        score = max(0.0, min(100.0, score))
        summary = str(evaluation['candidate_summary']).strip()

        if not summary:
            summary = "AI evaluation completed but returned no summary."

        return round(score, 2), summary

    except Exception as e:
        print("AI SCORING ERROR:", str(e))
        if result_text:
            try:
                print(_extract_json_string(result_text))
            except Exception:
                pass
        return 50.0, "AI evaluation was unavailable; manual review is recommended."


def _extract_json_string(text):
    """Extract the first JSON-like object from AI response text."""
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or start > end:
        raise ValueError("Could not find JSON object in AI response")
    return text[start:end + 1]