from document_tools import extract_pdf_pages
from exam_tools import extract_questions, count_topics

pdf_path = r"C:\Users\HP\Documents\Schoolar mind AI\sample.pdf"

pages = extract_pdf_pages(pdf_path)

questions = extract_questions(pages)

print("\nEXTRACTED QUESTIONS")
print("===================")

for item in questions:
    print(f"\nPage {item['page']}")
    print(item["question"][:500])

topics = [
    "database",
    "normalization",
    "network",
    "security",
    "machine learning",
    "operating system"
]

results = count_topics(questions, topics)

print("\nTOPIC FREQUENCY")
print("================")

for topic, count in results.most_common():
    print(f"{topic}: {count}")