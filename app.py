"""
JD-to-Resume Customizer
------------------------
Upload your resume + paste a job description -> get back a tailored,
ATS-optimized resume as a finished, downloadable PDF (not a chat reply).

Run locally:
    streamlit run app.py
"""

import os

import streamlit as st

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
    api_key = st.text_input(
        "Anthropic API Key",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        type="password",
        help="Get one at console.anthropic.com. Stored only for this session.",
    )
    st.markdown("---")
    st.markdown(
        "**How it works**\n"
        "1. Parse your resume file into plain text\n"
        "2. Claude rewrites/reorders it to match the JD (facts only — no fabrication)\n"
        "3. A keyword-overlap score shows before vs. after ATS match\n"
        "4. A polished PDF is generated for download"
    )

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Your resume")
    resume_file = st.file_uploader("Upload resume (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
    use_sample_resume = st.checkbox("Use sample resume instead", value=not resume_file)

with col2:
    st.subheader("2. Target job description")
    jd_text_input = st.text_area("Paste the JD text here", height=220)
    use_sample_jd = st.checkbox("Use sample JD instead", value=not jd_text_input)

run = st.button("✨ Tailor My Resume", type="primary", use_container_width=True)

if run:
    if not api_key:
        st.error("Please enter your Anthropic API key in the sidebar.")
        st.stop()

    # --- Load resume text ---
    if use_sample_resume or not resume_file:
        with open("sample_data/sample_resume.txt", "r") as f:
            resume_text = f.read()
    else:
        try:
            resume_text = extract_text(resume_file.read(), resume_file.name)
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

    with st.spinner("Tailoring your resume with Claude..."):
        try:
            tailored = tailor_resume(resume_text, jd_text, api_key=api_key)
        except Exception as e:
            st.error(f"Tailoring failed: {e}")
            st.stop()

    tailored_flat_text = " ".join([
        tailored.get("summary", ""),
        " ".join(tailored.get("skills", [])),
        " ".join(
            b for job in tailored.get("experience", []) for b in job.get("bullets", [])
        ),
    ])
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
