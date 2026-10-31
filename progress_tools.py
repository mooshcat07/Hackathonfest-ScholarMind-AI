
import json
from pathlib import Path
from datetime import datetime


HISTORY_FILE = Path(__file__).parent / "quiz_history.json"


def load_quiz_history():
    """Load previously saved quiz results."""

    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return []


def save_quiz_result(topic, score, total):
    """Save a completed quiz attempt."""

    history = load_quiz_history()

    percentage = (score / total) * 100 if total else 0

    attempt = {
        "topic": topic,
        "score": score,
        "total": total,
        "percentage": round(percentage, 2),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    history.append(attempt)

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)

    return attempt
