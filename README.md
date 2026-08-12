# JD-to-Resume Customizer

Upload a resume and paste a job description → get back a **tailored, ATS-optimized resume as a finished, downloadable PDF**. Not a chat reply, not a Gem — a working product.

## Why this approach

Most "AI resume tools" are a thin prompt wrapper: paste JD, paste resume, get back prose advice you then have to manually apply. That's not a product, it's a chat session. This tool instead:

1. **Parses** the uploaded resume file directly (PDF/DOCX/TXT → plain text)
2. **Tailors** it with an LLM constrained to a strict JSON schema and a hard rule: *rephrase, reorder, and re-emphasize truthfully — never fabricate* employers, titles, dates, or skills that aren't in the source resume
3. **Scores** ATS keyword match before vs. after, using a fast deterministic heuristic (not another LLM call) — so the "value add" is something concrete and measurable, not just a vibe
4. **Renders** the tailored content into a clean, single-column, ATS-safe PDF using `reportlab` — no LibreOffice/wkhtmltopdf dependency, so it's portable and fast

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌────────────────┐
│  Upload:    │────▶│ resume_parser.py │────▶│   tailor.py      │────▶│  pdf_builder.py │
│  resume +   │     │ (pdfplumber /    │     │ (Claude API,     │     │  (reportlab →   │
│  JD text    │     │  python-docx)    │     │  strict JSON     │     │   finished PDF) │
│             │     │                  │     │  schema)         │     │                 │
└─────────────┘     └──────────────────┘     └─────────────────┘     └────────────────┘
                                                       │
                                                       ▼
                                            keyword_match_score()
                                            (before/after ATS metric,
                                             pure Python, no LLM call)
```

- **`app.py`** — Streamlit UI: upload, JD input, run, preview, download
- **`core/resume_parser.py`** — file → plain text (PDF via `pdfplumber`, DOCX via `python-docx`)
- **`core/prompts.py`** — the system prompt enforcing the "no fabrication" schema
- **`core/tailor.py`** — calls the Claude API; also has `keyword_match_score()`, a cheap non-LLM heuristic for a before/after match percentage
- **`core/pdf_builder.py`** — structured JSON → polished PDF via `reportlab`

## Running it locally

```bash
git clone <your-repo-url>
cd jd-resume-customizer
pip install -r requirements.txt

cp .env.example .env
# edit .env and add your ANTHROPIC_API_KEY

streamlit run app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`). You can also enter your API key directly in the sidebar instead of using `.env`.

There are sample resume/JD files under `sample_data/` so you can demo it with one click, no uploads needed.

## Deploying a live demo

Easiest path: [Streamlit Community Cloud](https://streamlit.io/cloud) — connect this GitHub repo, set `ANTHROPIC_API_KEY` as a secret, deploy. Free, and gives you a public demo link for the submission form.

## Known limitations / what I'd do next with more time

- Resume parsing is text-only — doesn't preserve the original's visual layout intent (by design: the LLM re-derives structure). Complex multi-column resume PDFs can extract text out of order.
- No persistence/auth — it's a single-session tool. Adding user accounts + a history of tailored versions would be a natural next step.
- The keyword-match score is a simple overlap heuristic, not true ATS parsing behavior — good enough as a directional signal, but a v2 could use embedding similarity for semantic (not just literal) match.
- Currently one PDF template/design. Next: 2-3 selectable templates.
- Would add a "diff view" showing exactly which bullets/lines changed vs. the original, for full transparency.
