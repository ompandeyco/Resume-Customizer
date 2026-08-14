"""Output the original vs tailored resume for analysis."""
import os
import sys
import json
from dotenv import load_dotenv
sys.path.insert(0, ".")
from core.resume_parser import extract_text
from core.tailor import tailor_resume

load_dotenv()

def main():
    resume_path = r"E:\Downloads\OmPandeyResume.pdf"
    jd_path = "sample_data/sample_jd.txt"
    
    with open(resume_path, "rb") as f:
        original_text = extract_text(f.read(), "OmPandeyResume.pdf")
        
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()
        
    api_key = os.environ.get("GEMINI_API_KEY")
    tailored = tailor_resume(original_text, jd_text, provider="gemini", api_key=api_key)
    
    with open("resume_comparison.txt", "w", encoding="utf-8") as f:
        f.write("="*80 + "\n")
        f.write("ORIGINAL TEXT:\n")
        f.write("="*80 + "\n")
        f.write(original_text + "\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("TAILORED JSON OUTPUT:\n")
        f.write("="*80 + "\n")
        f.write(json.dumps(tailored, indent=2) + "\n")

if __name__ == "__main__":
    main()
