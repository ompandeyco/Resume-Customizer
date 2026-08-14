# 📄 JD-to-Resume Customizer

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini-8E75B2.svg)](https://deepmind.google/technologies/gemini/)

An AI-powered application that takes your existing resume and a target job description (JD), and automatically tailors your resume to match the JD's requirements. 

## ✨ Why is this different from a ChatGPT prompt?

Most people use ChatGPT to tailor their resumes by pasting their history and the JD into a chat window. This approach has three major flaws that this tool actively solves:

1. 🖨️ **Finished, ATS-Friendly PDF Output:** Chatbots spit out markdown text. You then have to spend 30 minutes copying, pasting, and reformatting that text into a Word doc or PDF. This app bypasses the chat entirely and generates a cleanly formatted, single-column, ATS-readable PDF ready for immediate download.
2. 🛡️ **Strict Anti-Fabrication Guardrails:** Standard LLMs will often hallucinate skills you don't have just because the JD asked for them. This tool uses structured output generation and a strict system prompt to ensure it *only* reorders, emphasizes, and rephrases your *actual* historical experience. It will not invent experience.
3. 📊 **Objective ATS Keyword Scoring:** How do you know the AI actually improved your resume? This app runs an independent, deterministic heuristic (keyword matching and bigram analysis) to show you a concrete "Before" and "After" overlap score. **Crucially, this score is computed independently of the LLM**, proving the tailoring was effective rather than just relying on the AI's own word for it.

## 🏗️ Pipeline Architecture

The application runs entirely locally using a Streamlit frontend and calls the Google Gemini API for the tailoring step.

```text
  [PDF/Word/TXT]        [Text Paste]
   User Resume       Job Description (JD)
        │                    │
        ▼                    ▼
 ┌───────────────────────────────────────┐
 │ 1. PARSE                              │
 │ Extracts raw text from the resume     │
 │ document using pdfplumber / docx.     │
 └───────────────────┬───────────────────┘
                     │
                     ▼
 ┌───────────────────────────────────────┐
 │ 2. TAILOR (Gemini API)                │
 │ Structured LLM call to generate JSON  │
 │ matching the schema of a resume while │
 │ adhering to anti-fabrication rules.   │
 └───────────────────┬───────────────────┘
                     │
                     ▼
 ┌───────────────────────────────────────┐
 │ 3. SCORE                              │
 │ Extracts technical bigrams & keywords │
 │ from the JD (minus filler) and scores │
 │ the raw vs. tailored resume.          │
 └───────────────────┬───────────────────┘
                     │
                     ▼
 ┌───────────────────────────────────────┐
 │ 4. RENDER                             │
 │ Converts the tailored JSON into a     │
 │ clean, ATS-compliant PDF via reportlab│
 └───────────────────────────────────────┘
                     │
                     ▼
             [Download PDF]
```

## 🚀 Local Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd jd-resume-customizer
   ```

2. **Install dependencies**
   Ensure you have Python 3.10 or higher installed.
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and paste your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_key_here
   ```

4. **Run the Application**
   ```bash
   streamlit run app.py
   ```
   The app will automatically open in your browser at `http://localhost:8501`.

## ☁️ Deployment (Streamlit Community Cloud)

You can easily host this for free on Streamlit Community Cloud:

1. Push this repository to a public or private GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3. Click **New app**.
4. Select your repository, branch, and set the main file path to `app.py`.
5. ⚠️ **CRITICAL:** Before clicking Deploy, click on **Advanced settings** and add your `GEMINI_API_KEY` to the Secrets section:
   ```toml
   GEMINI_API_KEY = "your_actual_key_here"
   ```
6. Click **Deploy**. Your app will be live with a public URL in a few minutes.

## 🚧 Known Limitations & Future Work

* **Heuristic Scoring vs. Semantic ATS:** The keyword scorer relies on a deterministic heuristic (word overlap and bigram analysis). It is not a true semantic matcher. For example, it will not natively know that "GCP" and "Google Cloud Platform" are the same thing. 
* **The "Score Drop" Phenomenon:** Because of the strict anti-fabrication guardrails, you may occasionally see the "After" score go *down*. This happens when the LLM tightens your bullet points for clarity (removing words that previously matched a JD keyword by coincidence) while refusing to fabricate a direct keyword match. **This is intentional: the tool prioritizes absolute accuracy and honesty over blindly gaming the metric.**
* **Hardcoded Styling:** The PDF builder (`reportlab`) currently produces a single hardcoded layout. It looks clean and professional, but future iterations should support uploading a LaTeX template or selecting from multiple design themes.
* **Context Window Limits:** Extremely long resumes or JDs might bump into context limits, though `gemini-3.5-flash` handles most standard sizes with ease.
