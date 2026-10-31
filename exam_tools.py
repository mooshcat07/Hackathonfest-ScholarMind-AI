
import re
from collections import Counter


def extract_questions(pages):
    """Extract numbered examination questions from PDF pages."""

    questions = []

    patterns = [
        r"(?im)^\s*(?:QUESTION|QUESTIONS|Q)\s*\d+\s*[\.\:\)]?",
        r"(?m)^\s*\d+\s*[\.\)]\s+\S",
    ]

    for page in pages:

        text = page["text"]

        matches = []

        for pattern in patterns:
            matches.extend(re.finditer(pattern, text))

        # Remove duplicate matches.
        unique_matches = {
            match.start(): match
            for match in matches
        }

        matches = sorted(
            unique_matches.values(),
            key=lambda match: match.start()
        )

        for index, match in enumerate(matches):

            start = match.start()

            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(text)
            )

            question = text[start:end].strip()

            if len(question) >= 20:

                questions.append({
                    "page": page["page"],
                    "question": question
                })

    return questions


def count_topics(questions, topics):
    """Count occurrences of supplied topics."""

    counts = Counter()

    for item in questions:

        question = item["question"].lower()

        for topic in topics:

            if topic.lower() in question:
                counts[topic] += 1

    return counts


def classify_exam_questions(questions, client, model):
    """Use AI to analyse and classify examination questions."""

    if not questions:
        return "No examination questions were extracted."

    question_text = ""

    for index, item in enumerate(questions, start=1):

        question_text += (
            f"\nQuestion {index} (Page {item['page']}):\n"
            f"{item['question'][:1000]}\n"
        )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """
You are ScholarMind's examination intelligence engine.

Analyse the supplied examination questions.

For each question identify:
1. Main academic topic.
2. Specific concept being tested.
3. Examination command word.
4. Cognitive skill being assessed.

Then provide:

- Topic classification.
- Recurring topics and concepts.
- Common examination command words.
- Suggested revision priorities.
- A short overall examination analysis.

Only use the supplied questions.

Do not invent question content.
Do not predict future examinations.
Clearly distinguish observed patterns from recommendations.
"""
            },
            {
                "role": "user",
                "content": question_text
            }
        ],
        temperature=0.2,
        max_tokens=700
    )

    return response.choices[0].message.content or ""
