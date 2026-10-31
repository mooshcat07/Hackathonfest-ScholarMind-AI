
import os
import json

from dotenv import load_dotenv
from groq import Groq

from tools import (
    calculate_average,
    calculate_weighted_average,
    calculate_percentage,
    calculate_required_mark
)

from progress_tools import save_quiz_result, load_quiz_history

from quiz_tools import generate_quiz, check_answer

from document_tools import (
    extract_pdf_pages,
    search_document
)

from exam_tools import (
    extract_questions,
    count_topics,
    classify_exam_questions
)


# ==========================================
# 1. CONFIGURATION
# ==========================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY was not found in .env.")

client = Groq(api_key=api_key)

MODEL = "qwen/qwen3.8-27b"


# ==========================================
# 2. AVAILABLE AI TOOLS
# ==========================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate_average",
            "description": "Calculate the simple average of three assessment marks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mark1": {"type": "number"},
                    "mark2": {"type": "number"},
                    "mark3": {"type": "number"}
                },
                "required": ["mark1", "mark2", "mark3"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_weighted_average",
            "description": "Calculate the weighted average of three assessments. Weights must total 100.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mark1": {"type": "number"},
                    "weight1": {"type": "number"},
                    "mark2": {"type": "number"},
                    "weight2": {"type": "number"},
                    "mark3": {"type": "number"},
                    "weight3": {"type": "number"}
                },
                "required": [
                    "mark1", "weight1",
                    "mark2", "weight2",
                    "mark3", "weight3"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_percentage",
            "description": "Calculate a percentage from obtained and total marks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "obtained": {"type": "number"},
                    "total": {"type": "number"}
                },
                "required": ["obtained", "total"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_required_mark",
            "description": "Calculate the required mark in a final assessment to reach a target overall mark. current_points represents weighted points already earned.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_points": {"type": "number"},
                    "final_weight": {"type": "number"},
                    "target": {"type": "number"}
                },
                "required": [
                    "current_points",
                    "final_weight",
                    "target"
                ]
            }
        }
    }
]


# ==========================================
# 3. TOOL EXECUTION ENGINE
# ==========================================

AVAILABLE_TOOLS = {
    "calculate_average": calculate_average,
    "calculate_weighted_average": calculate_weighted_average,
    "calculate_percentage": calculate_percentage,
    "calculate_required_mark": calculate_required_mark
}


def execute_tool(tool_call):

    tool_name = tool_call.function.name

    try:
        if tool_name not in AVAILABLE_TOOLS:
            raise ValueError("Tool not available.")

        arguments = json.loads(tool_call.function.arguments)

        result = AVAILABLE_TOOLS[tool_name](**arguments)

        return json.dumps({
            "success": True,
            "result": result
        })

    except Exception as error:

        return json.dumps({
            "success": False,
            "error": str(error)
        })


# ==========================================
# 4. CONVERSATION MEMORY
# ==========================================

SYSTEM_PROMPT = """
You are ScholarMind, an intelligent university academic mentor.

YOUR RESPONSIBILITIES:

1. Explain academic concepts clearly.
2. Help students understand examination questions.
3. Provide structured, step-by-step explanations.
4. Use practical examples where appropriate.
5. Encourage independent learning.
6. Help students improve their academic performance.
7. Generate practice questions and provide answers.
8. Identify knowledge gaps and explain difficult concepts.

AVAILABLE PYTHON TOOLS:

- calculate_average
- calculate_weighted_average
- calculate_percentage
- calculate_required_mark

TOOL RULES:

- Use the appropriate Python tool for calculations.
- Never invent calculation results.
- Explain calculation results clearly.
- Never invent university grading scales.
- Do not claim a distinction without an official grading scale.

DOCUMENT RULES:

- When document context is provided, prioritise that material.
- Do not invent document references or page numbers.
- Clearly explain when information is missing.

TEACHING STYLE:

- Explain concepts before giving complicated answers.
- Use examples relevant to university students.
- Keep answers structured and understandable.
- Encourage students to think independently.
"""

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


# ==========================================
# 5. DOCUMENT MEMORY
# ==========================================

loaded_pages = []
document_name = None


# ==========================================
# 6. AI RESPONSE ENGINE
# ==========================================

def ask_scholarmind(question):

    messages.append({
        "role": "user",
        "content": question
    })

    while True:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.5,
            max_tokens=700
        )

        assistant_message = response.choices[0].message

        if not assistant_message.tool_calls:

            answer = assistant_message.content or ""

            messages.append({
                "role": "assistant",
                "content": answer
            })

            if len(messages) > 21:
                messages[:] = [messages[0]] + messages[-20:]
            return answer

        # Store the assistant tool request.
        messages.append(
            assistant_message.model_dump(exclude_none=True)
        )

        # Execute each requested tool.
        for tool_call in assistant_message.tool_calls:

            tool_result = execute_tool(tool_call)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

# ==========================================
# 7. INTERACTIVE QUIZ ENGINE
# ==========================================

def show_progress():
    history = load_quiz_history()

    print("\n================================")
    print("       STUDENT PROGRESS")
    print("================================")

    if not history:
        print("No quiz history available yet.")
        print("Complete a quiz to start tracking progress.")
        return

    total_attempts = len(history)

    average = sum(
        attempt["percentage"] for attempt in history
    ) / total_attempts

    print(f"\nTotal quizzes completed: {total_attempts}")
    print(f"Overall average: {average:.1f}%")

    print("\nRECENT QUIZ ATTEMPTS")

    for attempt in reversed(history[-5:]):
        print(f"\nTopic: {attempt['topic']}")
        print(f"Score: {attempt['score']}/{attempt['total']}")
        print(f"Percentage: {attempt['percentage']}%")
        print(f"Date: {attempt['date']}")

def run_quiz(topic):

    print(f"\nScholarMind: Preparing your quiz on {topic}...")

    context = ""

    if loaded_pages:
        results = search_document(topic, loaded_pages, limit=3)

        for result in results:
            context += (
                f"\nPage {result['page']}: "
                f"{result['text'][:1500]}\n"
            )

    try:
        questions = generate_quiz(
            client,
            MODEL,
            topic,
            context
        )

        score = 0
        total = len(questions)
        missed_questions = []
        if total == 0:
            print("No quiz questions were generated.")
            return

        print("\n================================")
        print("       SCHOLARMIND QUIZ")
        print("================================")

        for index, question in enumerate(questions, start=1):

            print(f"\nQuestion {index}/{total}")
            print(question["question"])

            for option, text in question["options"].items():
                print(f"{option}. {text}")

            while True:
                answer = input("\nYour answer (A/B/C/D): ").strip().upper()

                if answer in question["options"]:
                    break

                print("Please enter A, B, C or D.")

            result = check_answer(question, answer)

            if result["correct"]:
                score += 1
                print("\nCorrect! Well done.")
            else:
                print("\nIncorrect.")
                missed_questions.append(question)

            print(f"Correct answer: {result['correct_answer']}")
            print(f"Explanation: {result['explanation']}")

        percentage = (score / total) * 100

        save_quiz_result(topic, score, total)
        print("\nQuiz result saved successfully!")

        print("\n================================")
        print("          QUIZ RESULTS")
        print("================================")

        print(f"Score: {score}/{total}")
        print(f"Percentage: {percentage:.1f}%")

        if percentage >= 80:
            print("Excellent understanding!")
        elif percentage >= 50:
            print("Good effort. Keep revising.")
        else:
            print("You should revisit this topic.")

        print("\n================================")
        print("       KNOWLEDGE GAP REPORT")
        print("================================")

        if missed_questions:
            print("You should revise these questions:")

            for index, question in enumerate(missed_questions, start=1):
                print(f"\n{index}. {question['question']}")
                print(f"Explanation: {question['explanation']}")

        else:
            print("Excellent! You answered every question correctly.")

    except Exception as error:
        print(f"\nQuiz failed: {error}")



# ==========================================
# 7. APPLICATION INTERFACE
# ==========================================

def show_help():

    print("""
SCHOLARMIND COMMANDS
DOCUMENT INTELLIGENCE
/load <pdf_path>   Load a PDF document
/ask <question>    Ask questions about the PDF
/exam              Extract examination questions
/topics            Analyse historical topic frequency
/analyse           AI examination intelligence

LEARNING TOOLS
/practice <topic>  Generate practice questions
/explain <topic>   Enter deep learning mode
/quiz <topic>       Start an interactive quiz

GENERAL
/clear             Clear conversation history
/help              Display commands
/exit              Close ScholarMind
/progress          View academic progress

EXAMPLE QUESTIONS

Explain object-oriented programming.
Calculate my average for 75, 65 and 80.
Generate five questions about database normalization.
Teach me how binary search works.
Help me understand REST APIs.
""")


print("\n================================")
print("       SCHOLARMIND AI")
print("  Your Personal Academic Mentor")
print("================================")

show_help()


# ==========================================
# 8. MAIN CONVERSATION LOOP
# ==========================================

while True:

    try:

        question = input("\nYou: ").strip()

        if not question:
            continue

        command = question.lower()

        # ----------------------------------
        # EXIT
        # ----------------------------------

        if command in ["/exit", "exit"]:

            print("\nScholarMind: Happy studying! Goodbye.")
            break

        # ----------------------------------
        # HELP
        # ----------------------------------

        if command == "/help":

            show_help()
            continue

        # ----------------------------------
        # CLEAR CONVERSATION
        # ----------------------------------

        if command == "/clear":

            messages = [messages[0]]

            print("\nScholarMind: Conversation history cleared.")
            continue

        # ----------------------------------
        # LOAD PDF
        # ----------------------------------

        if command.startswith("/load "):

            pdf_path = question[6:].strip().strip('"')

            try:

                pages = extract_pdf_pages(pdf_path)

                loaded_pages = pages
                document_name = os.path.basename(pdf_path)

                print(f"\nScholarMind: Loaded {document_name}")
                print(f"Pages extracted: {len(loaded_pages)}")

            except Exception as error:

                print(f"\nPDF loading failed: {error}")

            continue

        # ----------------------------------
        # ASK QUESTIONS ABOUT PDF
        # ----------------------------------

        if command.startswith("/ask "):

            if not loaded_pages:

                print("\nScholarMind: Please load a PDF first.")
                continue

            academic_question = question[5:].strip()

            if not academic_question:
                print("\nPlease enter a question.")
                continue

            try:

                results = search_document(
                    academic_question,
                    loaded_pages,
                    limit=3
                )

                if not results:

                    print("\nScholarMind: No relevant information was found.")
                    continue

                context = ""

                for result in results:

                    context += (
                        f"\nDOCUMENT: {document_name}\n"
                        f"PAGE: {result['page']}\n"
                        f"{result['text'][:2500]}\n"
                    )

                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": """
You are ScholarMind.

Answer using the supplied document context.

Explain concepts clearly and step by step.
Cite the supplied document page numbers.
Never invent information or references.

If the context is insufficient, say so.
"""
                        },
                        {
                            "role": "user",
                            "content": f"""
DOCUMENT CONTEXT:
{context}

STUDENT QUESTION:
{academic_question}
"""
                        }
                    ],
                    temperature=0.4,
                    max_tokens=700
                )

                answer = response.choices[0].message.content or ""

                print(f"\nScholarMind: {answer}")

            except Exception as error:

                print(f"\nDocument question failed: {error}")

            continue

        # ----------------------------------
        # EXAMINATION QUESTION EXTRACTION
        # ----------------------------------

        if command == "/exam":

            if not loaded_pages:

                print("\nScholarMind: Load a past paper first.")
                continue

            questions = extract_questions(loaded_pages)

            print("\nEXAMINATION INTELLIGENCE")
            print("========================")

            print(f"Document: {document_name}")
            print(f"Questions extracted: {len(questions)}")

            for index, item in enumerate(questions, start=1):

                print(f"\nQuestion {index} (Page {item['page']})")
                print(item["question"][:1000])

            continue

        # ----------------------------------
        # TOPIC FREQUENCY
        # ----------------------------------
        
        # ----------------------------------
        # AI EXAMINATION INTELLIGENCE
        # ----------------------------------

        if command == "/analyse":

            if not loaded_pages:
                print("\nScholarMind: Load a past paper first.")
                continue

            questions = extract_questions(loaded_pages)

            if not questions:
                print("\nNo examination questions were extracted.")
                print("Check the PDF text and question formatting.")
                continue

            print("\nScholarMind: Analysing examination paper...")
            print(f"Questions identified: {len(questions)}")

            try:
                analysis = classify_exam_questions(
                    questions,
                    client,
                    MODEL
                )

                print("\n================================")
                print("    EXAMINATION INTELLIGENCE")
                print("================================")
                print(analysis)

            except Exception as error:
                print(f"\nAnalysis failed: {error}")

            continue

        # ----------------------------------
        # TOPIC FREQUENCY
        # ----------------------------------
        if command == "/topics":

            if not loaded_pages:

                print("\nScholarMind: Load a past paper first.")
                continue

            questions = extract_questions(loaded_pages)

            topics = [
                "database",
                "normalization",
                "network",
                "security",
                "machine learning",
                "operating system",
                "programming",
                "software engineering",
                "artificial intelligence",
                "data structures"
            ]

            results = count_topics(questions, topics)

            print("\nTOPIC FREQUENCY ANALYSIS")
            print("========================")

            if not results:

                print("No matching topics were found.")

            else:

                for topic, count in results.most_common():

                    print(f"{topic}: {count}")

            print(
                "\nNote: These are historical document frequencies, "
                "not predictions of future examinations."
            )

            continue

        # ----------------------------------
        # PRACTICE QUESTION GENERATOR
        # ----------------------------------

        if command.startswith("/practice "):

            topic = question[10:].strip()

            if not topic:

                print("\nPlease provide a topic.")
                continue

            context = ""

            if loaded_pages:

                results = search_document(
                    topic,
                    loaded_pages,
                    limit=3
                )

                for result in results:

                    context += (
                        f"\nPage {result['page']}: "
                        f"{result['text'][:2000]}\n"
                    )

            prompt = f"""
Generate five university-level practice questions about:

{topic}

DOCUMENT MATERIAL:
{context if context else "No document has been loaded. Use your general academic knowledge."}

For each question:
- Test understanding and application.
- Include a suitable mark allocation.
- Use varied command words.
- Do not pretend these questions appeared in an actual examination.

At the end, provide a separate answer guide.
"""

            print("\nScholarMind: Generating practice questions...")

            answer = ask_scholarmind(prompt)

            print(f"\nScholarMind:\n{answer}")

            continue

        # ----------------------------------
        # DEEP LEARNING MODE
        # ----------------------------------

        if command.startswith("/explain "):

            topic = question[9:].strip()

            if not topic:

                print("\nPlease provide a topic.")
                continue

            prompt = f"""
Enter DEEP LEARNING MODE.

Teach me: {topic}

Follow this teaching structure:

1. Start with a clear definition.
2. Explain the fundamental concepts.
3. Break down how it works.
4. Give a practical example.
5. Explain real-world applications.
6. Identify common misunderstandings.
7. Finish with three comprehension questions.

Teach at university level, but explain difficult ideas simply.
Do not skip foundational concepts.
"""

            print("\nScholarMind: Entering Deep Learning Mode...")

            answer = ask_scholarmind(prompt)

            print(f"\nScholarMind:\n{answer}")

            continue

        # ----------------------------------
        # INTERACTIVE QUIZ MODE
        # ----------------------------------

        if command.startswith("/quiz "):

            topic = question[6:].strip()

            if not topic:
                print("\nPlease provide a quiz topic.")
                continue

            run_quiz(topic)
            continue
        
        if command == "/progress":
            show_progress()
            continue

        # ----------------------------------
        # NORMAL AI CONVERSATION
        # ----------------------------------

        print("\nScholarMind is thinking...")

        answer = ask_scholarmind(question)

        print(f"\nScholarMind: {answer}")

        # Keep conversation history manageable.
        if len(messages) > 21:

            messages = [messages[0]] + messages[-20:]

    except KeyboardInterrupt:

        print("\n\nScholarMind closed.")
        break

    except Exception as error:

        print(f"\nRequest failed: {error}")
        print("Please try again.")
