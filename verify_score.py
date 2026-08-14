"""Run keyword_match_score on the newly tailored (anti-fabricated) resume."""
import os
import sys
import logging
from dotenv import load_dotenv

sys.path.insert(0, ".")
from core.resume_parser import extract_text
from core.tailor import tailor_resume, keyword_match_score

load_dotenv()
logging.basicConfig(level=logging.ERROR)

def main():
    resume_path = r"E:\Downloads\OmPandeyResume.pdf"
    jd_path = "sample_data/sample_jd.txt"
    
    with open(resume_path, "rb") as f:
        original_text = extract_text(f.read(), "OmPandeyResume.pdf")
        
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()
        
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # 1. Get before score
    before = keyword_match_score(original_text, jd_text)
    
    # 2. Tailor
    tailored = tailor_resume(original_text, jd_text, provider="gemini", api_key=api_key)
    
    # 3. Build flat text correctly (title, projects, education included)
    flat_parts = [
        tailored.get("name", ""),
        tailored.get("title", ""),
        tailored.get("summary", ""),
        " ".join(tailored.get("skills", [])),
    ]
    for job in tailored.get("experience", []):
        flat_parts.append(job.get("role", ""))
        flat_parts.append(job.get("company", ""))
        flat_parts.extend(job.get("bullets", []))
    for proj in tailored.get("projects", []):
        flat_parts.append(proj.get("name", ""))
        flat_parts.append(proj.get("description", ""))
        flat_parts.extend(proj.get("bullets", []))
    for edu in tailored.get("education", []):
        flat_parts.append(edu.get("school", ""))
        flat_parts.append(edu.get("degree", ""))
    
    tailored_flat_text = " ".join(flat_parts)
    
    # 4. Get after score
    after = keyword_match_score(tailored_flat_text, jd_text)
    
    print("=== BEFORE TAILORING ===")
    print(f"Score: {before['score']}%")
    print(f"Matched ({len(before['matched_keywords'])}): {before['matched_keywords']}")
    print(f"Missing ({len(before['missing_keywords'])}): {before['missing_keywords']}")
    print("\n=== AFTER TAILORING (with strict anti-fabrication) ===")
    print(f"Score: {after['score']}%")
    print(f"Matched ({len(after['matched_keywords'])}): {after['matched_keywords']}")
    print(f"Missing ({len(after['missing_keywords'])}): {after['missing_keywords']}")
    
    print(f"\nImprovement: {before['score']}% -> {after['score']}% (+{after['score'] - before['score']}%)")

if __name__ == "__main__":
    main()
