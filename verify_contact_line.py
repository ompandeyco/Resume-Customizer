"""Test PDF rendering of contact line with empty linkedin field."""
import sys
import pdfplumber
sys.path.insert(0, ".")
from core.pdf_builder import build_resume_pdf

test_resume = {
    "name": "OM PANDEY",
    "title": "AI Engineer Intern",
    "contact": {
        "email": "omompandey7@gmail.com",
        "phone": "+91-9335878761",
        "location": "Azamgarh, Uttar Pradesh",
        "linkedin": ""
    },
    "summary": "Software Engineer and AI/ML Developer.",
    "skills": ["Python", "FastAPI"],
    "experience": [],
    "education": [],
    "projects": []
}

pdf_bytes = build_resume_pdf(test_resume)

with open("test_output_contact.pdf", "wb") as f:
    f.write(pdf_bytes)

print("Generated PDF.")
print("Extracting text from PDF to verify contact line...")

with pdfplumber.open("test_output_contact.pdf") as pdf:
    page = pdf.pages[0]
    text = page.extract_text()
    
    # Print the first few lines to show the header block
    lines = text.split("\n")
    print("\n--- Header Block from PDF ---")
    for i, line in enumerate(lines[:5]):
        print(f"Line {i+1}: {line}")
    print("-----------------------------\n")
