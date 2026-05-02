import json
from django.conf import settings
from openai import OpenAI

from hr_officer.models import Vacancy


def generate_exam_questions(
    vacancy: Vacancy,
    num_questions: int = 10,
    difficulty: str = 'medium',
    mcq_count: int | None = None,
    short_answer_count: int | None = None,
) -> list[dict]:
    """
    Generate ACADEMIC exam questions (NOT HR/Recruitment related).
    Fully safe against malformed AI responses.
    """

    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=settings.GITHUB_TOKEN
    )

    # ----------------------------
    # ACADEMIC-FOCUSED PROMPT
    # ----------------------------
    prompt = (
        "You are an expert academic exam question writer.\n"
        "Generate UNIVERSITY or PROFESSIONAL LEVEL EXAM QUESTIONS ONLY.\n\n"

        "🚫 STRICTLY FORBIDDEN:\n"
        "- HR questions\n"
        "- Recruitment/eligibility questions\n"
        "- CGPA, experience, salary, age, or application rules\n\n"

        "✅ REQUIRED:\n"
        "- Only field-of-study / subject knowledge questions\n"
        "- MCQs and short-answer conceptual questions\n"
        "- University exam style questions\n\n"

        "Return ONLY valid JSON:\n"
        "{{\n"
        "  \"questions\": [\n"
        "    {{\n"
        "      \"text\": \"What is the capital of France?\",\n"
        "      \"question_type\": \"MCQ\",\n"
        "      \"choices\": [\"Paris\", \"Madrid\", \"Berlin\", \"Rome\"],\n"
        "      \"correct_answer\": \"Paris\"\n"
        "    }},\n"
        "    {{\n"
        "      \"text\": \"Explain the role of photosynthesis in plant energy production.\",\n"
        "      \"question_type\": \"SHORT_ANSWER\"\n"
        "    }}\n"
        "  ]\n"
        "}}\n\n"

        "EXAM CONTEXT:\n"
        "Subject: {subject}\n"
        "Department: {department}\n"
        "Difficulty: {difficulty}\n"
        "Number of questions: {num_questions}\n"
        "MCQ count: {mcq_count}\n"
        "Short answer count: {short_answer_count}\n"
    ).format(
        subject=vacancy.employee_request.subject,
        department=vacancy.employee_request.department.name if vacancy.employee_request.department else "General",
        difficulty=difficulty.title(),
        num_questions=num_questions,
        mcq_count=mcq_count or 0,
        short_answer_count=short_answer_count or 0,
    )

    # ----------------------------
    # OPENAI CALL
    # ----------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate ONLY academic exam questions. "
                    "Never generate HR or recruitment content."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
    )

    text = response.choices[0].message.content.strip()

    # ----------------------------
    # SAFE JSON CLEANING
    # ----------------------------
    if "```" in text:
        text = text.replace("```json", "").replace("```", "").strip()

    # ----------------------------
    # SAFE JSON PARSING
    # ----------------------------
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find('{')
        end = text.rfind('}')

        if start == -1 or end == -1:
            return []

        try:
            payload = json.loads(text[start:end + 1])
        except Exception:
            return []

    # ----------------------------
    # SAFE QUESTION EXTRACTION
    # ----------------------------
    questions = payload.get("questions") or []

    validated = []

    for q in questions:
        if not isinstance(q, dict):
            continue

        q_text = q.get("text")
        q_type = q.get("question_type", "MCQ")

        if not q_text or not isinstance(q_text, str):
            continue

        q_text = q_text.strip()
        q_type = str(q_type).strip().upper().replace('-', '_')
        if q_type == 'SHORTANSWER':
            q_type = 'SHORT_ANSWER'

        # ---------------- MCQ ----------------
        if q_type == "MCQ":
            choices = q.get("choices")

            if not isinstance(choices, list):
                continue

            normalized_choices = []
            seen = set()
            for item in choices:
                if not isinstance(item, str):
                    continue
                text_choice = item.strip()
                if not text_choice:
                    continue
                key = text_choice.lower()
                if key not in seen:
                    seen.add(key)
                    normalized_choices.append(text_choice)

            if len(normalized_choices) < 4:
                continue

            correct = q.get("correct_answer")
            if isinstance(correct, str):
                correct = correct.strip()
            else:
                correct = None

            if correct:
                for item in normalized_choices:
                    if item.strip().lower() == correct.lower():
                        correct = item
                        break

            if not correct and len(normalized_choices) >= 4:
                correct = normalized_choices[0]

            if correct not in normalized_choices:
                if len(normalized_choices) > 4 and any(item.strip().lower() == correct.lower() for item in normalized_choices):
                    normalized_choices = [item for item in normalized_choices if item.strip().lower() != correct.lower()]
                    normalized_choices = normalized_choices[:3] + [correct]
                else:
                    continue

            if len(normalized_choices) > 4:
                if correct in normalized_choices[:4]:
                    normalized_choices = normalized_choices[:4]
                else:
                    normalized_choices = [correct] + [item for item in normalized_choices if item != correct][:3]

            if len(normalized_choices) != 4:
                continue

            validated.append({
                "text": q_text,
                "question_type": "MCQ",
                "choices": normalized_choices,
                "correct_answer": correct,
            })
            continue

        # ---------------- SHORT ANSWER ----------------
        if q_type == "SHORT_ANSWER":
            validated.append({
                "text": q_text,
                "question_type": "SHORT_ANSWER",
            })
            continue

        # ---------------- FALLBACK (safe MCQ conversion) ----------------
        choices = q.get("choices")

        if isinstance(choices, list):
            choices = [c.strip() for c in choices if isinstance(c, str)][:4]
        else:
            choices = []

        if len(choices) == 4:
            correct = q.get("correct_answer")

            if correct and correct in choices:
                validated.append({
                    "text": q_text,
                    "question_type": "MCQ",
                    "choices": choices,
                    "correct_answer": correct.strip(),
                })

    return validated