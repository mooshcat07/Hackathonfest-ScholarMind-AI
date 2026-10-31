
import json


def generate_quiz(client, model, topic, context=""):
    """Generate exactly five university-level quiz questions."""

    prompt = f"""
Create exactly FIVE university-level multiple-choice questions
about: {topic}

STUDY MATERIAL:
{context if context else "Use your academic knowledge."}

Return ONLY a valid JSON object using this structure:

{{
    "questions": [
        {{
            "question": "Question text",
            "options": {{
                "A": "Option A",
                "B": "Option B",
                "C": "Option C",
                "D": "Option D"
            }},
            "correct_answer": "A",
            "explanation": "Brief explanation of the correct answer."
        }}
    ]
}}

IMPORTANT RULES:
1. Generate exactly five questions.
2. Every question must have exactly four options: A, B, C and D.
3. Only one answer must be correct.
4. correct_answer must contain only A, B, C or D.
5. Keep explanations concise.
6. Cover different aspects of the topic.
7. Return all five questions in the same JSON object.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an academic quiz generator. "
                    "Return a valid JSON object containing exactly "
                    "five multiple-choice questions."
                )
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=1200
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("The AI returned an empty response.")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"The AI returned invalid JSON: {error}"
        ) from error

    questions = data.get("questions")

    if not isinstance(questions, list):
        raise ValueError("The AI response does not contain a questions list.")

    if len(questions) != 5:
        raise ValueError(
            f"The AI generated {len(questions)} questions instead of 5."
        )

    required_options = {"A", "B", "C", "D"}

    for index, question in enumerate(questions, start=1):

        if not all(
            key in question
            for key in ["question", "options", "correct_answer", "explanation"]
        ):
            raise ValueError(f"Question {index} is missing required fields.")

        if not isinstance(question["options"], dict):
            raise ValueError(f"Question {index} has invalid options.")

        if set(question["options"].keys()) != required_options:
            raise ValueError(
                f"Question {index} must have options A, B, C and D."
            )

        answer = question["correct_answer"].upper()

        if answer not in required_options:
            raise ValueError(
                f"Question {index} has an invalid correct answer."
            )

        question["correct_answer"] = answer

    return questions


def check_answer(question, student_answer):
    """Check whether the selected answer is correct."""

    correct = question["correct_answer"].upper()
    selected = student_answer.upper()

    return {
        "correct": selected == correct,
        "correct_answer": correct,
        "explanation": question["explanation"]
    }
