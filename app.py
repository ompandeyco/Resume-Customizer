"""
JD-to-Resume Customizer
------------------------
Upload your resume + paste a job description -> get back a tailored,
ATS-optimized resume as a finished, downloadable PDF (not a chat reply).

Run locally:
    streamlit run app.py
"""

import logging
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from core.pdf_builder import build_resume_pdf
from core.resume_parser import extract_text
from core.tailor import keyword_match_score, tailor_resume

st.set_page_config(page_title="JD-to-Resume Customizer", page_icon="📄", layout="wide")

st.title("📄 JD-to-Resume Customizer")
st.caption(
    "Upload your resume, paste a job description, and get a tailored, "
    "ATS-optimized resume as a finished PDF — not just chat advice."
)

with st.sidebar:
    st.header("Setup")
    st.markdown(
        "**How it works**\n"
        "1. Parse your resume file into plain text\n"
        "2. The LLM rewrites/reorders it to match the JD (facts only — no fabrication)\n"
        "3. A keyword-overlap score shows before vs. after ATS match\n"
        "4. A polished PDF is generated for download"
    )

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Your resume")
    resume_file = st.file_uploader("Upload resume (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
    resume_text_input = st.text_area("Or paste your resume text here", height=150)
    use_sample_resume = st.checkbox("Use sample resume instead", value=not (resume_file or resume_text_input))

with col2:
    st.subheader("2. Target job description")
    jd_text_input = st.text_area("Paste the JD text here", height=220)
    use_sample_jd = st.checkbox("Use sample JD instead", value=not jd_text_input)

run = st.button("✨ Tailor My Resume", type="primary", use_container_width=True)

if run:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.error("Please set GEMINI_API_KEY in your .env file.")
        st.stop()

    # --- Load resume text ---
    if use_sample_resume or (not resume_file and not resume_text_input.strip()):
        with open("sample_data/sample_resume.txt", "r") as f:
            resume_text = f.read()
    elif resume_text_input.strip():
        resume_text = resume_text_input
        logging.info(f"Text pasted: length {len(resume_text)} | First 200 chars: {repr(resume_text[:200])}")
    else:
        try:
            file_bytes = resume_file.read()
            logging.info(f"File upload: {resume_file.name} | Byte size: {len(file_bytes)}")
            resume_text = extract_text(file_bytes, resume_file.name)
            logging.info(f"Extracted text length: {len(resume_text)} | First 200 chars: {repr(resume_text[:200])}")
        except Exception as e:
            st.error(f"Couldn't read resume file: {e}")
            st.stop()

    # --- Load JD text ---
    if use_sample_jd or not jd_text_input.strip():
        with open("sample_data/sample_jd.txt", "r") as f:
            jd_text = f.read()
    else:
        jd_text = jd_text_input

    if not resume_text.strip():
        st.error("Resume text came out empty — try a different file.")
        st.stop()

    before = keyword_match_score(resume_text, jd_text)

    logging.info(f"Preparing to call API. Resume text length: {len(resume_text)}, JD text length: {len(jd_text)}")
    with st.spinner("Tailoring your resume with Gemini..."):
        try:
            tailored = tailor_resume(resume_text, jd_text, provider="gemini", api_key=api_key)
        except Exception as e:
            st.error(f"Tailoring failed: {e}")
            st.stop()

    # Build flat text from ALL tailored content for accurate scoring.
    # The old code only included summary + skills + experience bullets,
    # which dropped projects, education, title, and role/company names —
    # causing the "after" score to look artificially lower.
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
    after = keyword_match_score(tailored_flat_text, jd_text)

    st.success("Done! Here's the before/after ATS keyword match:")

    m1, m2 = st.columns(2)
    m1.metric("Before tailoring", f"{before['score']}%")
    m2.metric("After tailoring", f"{after['score']}%", delta=f"{after['score'] - before['score']}%")

    with st.expander("See matched / still-missing JD keywords"):
        st.write("**Matched after tailoring:**", ", ".join(after["matched_keywords"]) or "—")
        st.write("**Still missing:**", ", ".join(after["missing_keywords"]) or "—")

    st.subheader("Preview")
    st.markdown(f"### {tailored.get('name', '')}")
    st.markdown(f"*{tailored.get('title', '')}*")
    st.markdown(tailored.get("summary", ""))
    st.markdown("**Skills:** " + ", ".join(tailored.get("skills", [])))
    for job in tailored.get("experience", []):
        st.markdown(f"**{job.get('role', '')} — {job.get('company', '')}** ({job.get('dates', '')})")
        for b in job.get("bullets", []):
            st.markdown(f"- {b}")

    pdf_bytes = build_resume_pdf(tailored)
    st.download_button(
        "⬇️ Download tailored resume (PDF)",
        data=pdf_bytes,
        file_name=f"{tailored.get('name', 'resume').replace(' ', '_')}_tailored.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )
