from document_tools import extract_pdf_pages, search_document

# Replace this with the path to one of your PDF files.
PDF_PATH = r"C:\Users\HP\Documents\Schoolar mind AI\sample.pdf"

pages = extract_pdf_pages(PDF_PATH)

print(f"\nDocument loaded successfully!")
print(f"Pages extracted: {len(pages)}")

print("\n--- First page preview ---")
print(pages[0]["text"][:1000])

# Test document searching.
results = search_document("machine learning", pages)

print("\n--- Search Results ---")

for result in results:
    print(f"\nPage: {result['page']}")
    print(f"Relevance score: {result['score']}")
    print(result["text"][:500])