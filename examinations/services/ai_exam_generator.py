import json
from django.conf import settings
from openai import OpenAI

from hr_officer.models import Vacancy


def _normalize_counts(num_questions: int, mcq_count: int | None, short_answer_count: int | None) -> tuple[int, int, int]:
    if mcq_count is None:
        mcq_count = num_questions
    if short_answer_count is None:
        short_answer_count = max(0, num_questions - mcq_count)
    if mcq_count + short_answer_count != num_questions:
        short_answer_count = max(0, num_questions - mcq_count)
    return num_questions, mcq_count, short_answer_count


def _dedupe_questions(questions: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for q in questions:
        key = (
            q.get('text', '').strip(),
            q.get('question_type'),
            tuple(q.get('choices') or []),
            q.get('correct_answer'),
        )
        if key not in seen:
            seen.add(key)
            unique.append(q)
    return unique




def _count_question_types(questions: list[dict]) -> tuple[int, int]:
    mcq_count = sum(1 for q in questions if q.get('question_type') == 'MCQ')
    short_answer_count = sum(1 for q in questions if q.get('question_type') == 'SHORT_ANSWER')
    return mcq_count, short_answer_count


def _is_valid_question_set(questions: list[dict], num_questions: int, mcq_count_target: int, short_answer_count_target: int) -> bool:
    if len(questions) != num_questions:
        return False
    mcq_count, short_answer_count = _count_question_types(questions)
    return mcq_count == mcq_count_target and short_answer_count == short_answer_count_target


def generate_exam_questions(
    vacancy: Vacancy,
    num_questions: int = 10,
    difficulty: str = 'medium',
    mcq_count: int | None = None,
    short_answer_count: int | None = None,
) -> list[dict]:

    num_questions, mcq_count, short_answer_count = _normalize_counts(
        num_questions,
        mcq_count,
        short_answer_count,
    )

    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=settings.GITHUB_TOKEN
    )

    def _build_prompt(retry: bool = False) -> str:
        prompt = (
            "You are an expert academic exam question writer.\n"
            "Generate UNIVERSITY or PROFESSIONAL LEVEL EXAM QUESTIONS ONLY.\n\n"

            "🚫 STRICTLY FORBIDDEN:\n"
            "- HR questions\n"
            "- Recruitment questions\n"
            "- Eligibility questions\n\n"

            "✅ REQUIRED:\n"
            "- Only subject knowledge questions\n"
            "- University exam style\n"
            "- No placeholder questions or filler text\n"
            "- Do not use example text in the final output\n\n"

            "Return ONLY valid JSON.\n"
            "Return EXACTLY {num_questions} questions.\n"
            "Ensure exactly {mcq_count} MCQ and {short_answer_count} short-answer questions.\n"
            "Do not provide any extra explanation or markdown.\n\n"

            "MCQ RULES:\n"
            "- Each MCQ must have exactly 4 choices\n"
            "- Correct answer must be ONLY A, B, C, or D\n"
            "- Do not output placeholder choices like Option 1, Option 2, etc.\n\n"

            "Return JSON using this format:\n"
            "{{\n"
            "  \"questions\": [\n"
            "    {{\n"
            "      \"text\": \"A real question\",\n"
            "      \"question_type\": \"MCQ\",\n"
            "      \"choices\": [\"Choice A\", \"Choice B\", \"Choice C\", \"Choice D\"],\n"
            "      \"correct_answer\": \"A\"\n"
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

        if retry:
            prompt += (
                "\nThe previous response was incomplete or invalid. Generate again exactly the requested questions.\n"
                "Do not output placeholders or partial results.\n"
            )

        return prompt

    def _parse_questions(text: str) -> list[dict]:
        if "```" in text:
            text = text.replace("```json", "").replace("```", "").strip()

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

            if q_type == "MCQ":
                choices = q.get("choices")
                if not isinstance(choices, list):
                    continue

                choices = [c.strip() for c in choices if isinstance(c, str)][:4]
                if len(choices) != 4:
                    continue

                correct = str(q.get("correct_answer", "")).strip().upper()
                if correct not in ["A", "B", "C", "D"]:
                    continue

                validated.append({
                    "text": q_text,
                    "question_type": "MCQ",
                    "choices": choices,
                    "correct_answer": correct,
                })
                continue

            if q_type == "SHORT_ANSWER":
                validated.append({
                    "text": q_text,
                    "question_type": "SHORT_ANSWER",
                })
                continue

        validated = _dedupe_questions(validated)
        if not _is_valid_question_set(validated, num_questions, mcq_count, short_answer_count):
            return []

        return validated

    for attempt in range(2):
        prompt = _build_prompt(retry=(attempt == 1))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You generate ONLY academic exam questions."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )

        text = response.choices[0].message.content.strip()
        validated = _parse_questions(text)
        if validated:
            return validated

    return []