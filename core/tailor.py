"""
Core AI logic:
1. tailor_resume()      -> calls Gemini to produce a structured, JD-tailored
                            resume (JSON) from raw resume text + JD text.
2. keyword_match_score() -> a cheap, deterministic (non-LLM) ATS-style
                            keyword overlap score, used to show a concrete
                            "before vs after" improvement number in the UI.
"""

import json
import logging
import os
import re
from collections import Counter

from core.prompts import SYSTEM_PROMPT, build_user_prompt

# ─── Stopwords ──────────────────────────────────────────────────────────
# Standard English stopwords PLUS generic resume/JD filler words that add
# noise to a keyword-overlap score because they appear in virtually every
# posting regardless of skill match.
_STOPWORDS = set("""
a an the and or but if then else for of to in on at by with from as is are
was were be been being this that these those it its it's you your our we
they their he she his her i my me will would can could should shall may
might must not no yes do does did doing have has had having up down out
over under again further once here there all any both each few more most
other some such only own same so than too very s t just don don't now
""".split())

# Resume/JD filler: these are verbs and nouns that sound meaningful but
# appear in nearly every JD and resume regardless of role.
_RESUME_JD_FILLER = set("""
ship shipping work working works team teams build building builds help
helping helps looking look similar use using used able ability ensure
ensuring create creating maintain maintaining manage managing take taking
collaborate collaborating closely directly idea ideas fast quickly scope
prioritize features feature products product managers manager days months
years strong bonus track usage role company responsibilities requirements
based feedback iterate well end-to-end end clean write writing written
across new leverage deliver delivering key drive driving join projects
project experience experiences candidate candidates preferred responsible
like tasks task demo prototype prototypes integrate integrating
applications application instrument design designing tools tool
fundamentals familiarity understanding knowledge proficient proficiency
""".split())

_STOPWORDS |= _RESUME_JD_FILLER

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#]{1,}(?:-[a-zA-Z0-9+#]+)*")


def _extract_company_words(jd_text: str) -> set[str]:
    """Heuristically pull company/team proper nouns from the JD's first line
    (typically the job title line, e.g. 'AI Engineer Intern — PW Central AI
    Team') so we don't penalize candidates for not mentioning the company."""
    first_line = jd_text.strip().split("\n")[0]
    # Split on common title-company separators: em-dash, en-dash, pipe, @,
    # or any cluster of non-alphanumeric, non-space chars (handles encoding
    # variations of — and – gracefully).
    parts = re.split(r"\s*(?:[|@]|[^\w\s]{2,})\s*", first_line)
    company_words: set[str] = set()
    if len(parts) >= 2:
        # Everything after the separator is likely the company/team name
        company_part = " ".join(parts[1:])
        for w in _WORD_RE.findall(company_part):
            wl = w.lower()
            # Only strip short proper-noun fragments; keep real skills that
            # might appear in a company name by accident (e.g. "AI")
            if len(wl) >= 2 and wl not in {"ai", "ml", "llm", "nlp"}:
                company_words.add(wl)
    return company_words


def _extract_bigrams(text: str) -> list[str]:
    """Extract meaningful 2-word technical phrases from text."""
    words = _WORD_RE.findall(text)
    bigrams = []
    for i in range(len(words) - 1):
        phrase = f"{words[i]} {words[i+1]}".lower()
        bigrams.append(phrase)
    return bigrams


# Known technical bigrams worth scoring as single units.
# These are common multi-word terms that lose meaning when split.
_TECH_BIGRAMS = {
    "rest apis", "llm apis", "machine learning", "deep learning",
    "web scraping", "data pipelines", "data extraction",
    "prompt engineering", "prompt design", "content generation",
    "natural language", "computer vision", "cloud deployment",
    "ci cd", "test coverage", "api endpoints",
    "agentic ai", "generative ai", "structured output",
    "vector databases", "hugging face", "google cloud",
}


def _keywords(text: str, top_n: int = 40, exclude: set[str] | None = None) -> list[str]:
    """Extract the top-N meaningful keywords from text, returning both
    single words and recognized bigrams. Company words in `exclude` are
    dropped."""
    exclude = exclude or set()

    # --- Bigrams first (higher signal) ---
    text_bigrams = _extract_bigrams(text)
    bigram_counts = Counter(b for b in text_bigrams if b in _TECH_BIGRAMS)

    # --- Single words ---
    words = [w.lower() for w in _WORD_RE.findall(text)]
    words = [w for w in words
             if w not in _STOPWORDS
             and w not in exclude
             and len(w) > 2]
    word_counts = Counter(words)

    # Suppress single words that are already fully covered by a matched
    # bigram (e.g. don't count "rest" + "apis" separately if "rest apis"
    # already matched).
    covered_singles: set[str] = set()
    for bigram in bigram_counts:
        for part in bigram.split():
            covered_singles.add(part)

    filtered_words = [(w, c) for w, c in word_counts.most_common(top_n + 20)
                      if w not in covered_singles]

    # Merge: bigrams first (sorted by count desc), then remaining singles
    result: list[str] = []
    for bg, _ in bigram_counts.most_common(10):
        result.append(bg)
    for w, _ in filtered_words:
        if len(result) >= top_n:
            break
        result.append(w)

    return result[:top_n]


def keyword_match_score(resume_text: str, jd_text: str) -> dict:
    """Returns overlap between the JD's top keywords and the resume text.
    Supports both single-word and bigram matching. Company-specific words
    from the JD are excluded. This is a simple heuristic (not the LLM) so
    the score is fast, free, and deterministic — useful as a concrete
    before/after metric."""
    company_words = _extract_company_words(jd_text)
    jd_top_keywords = _keywords(jd_text, top_n=25, exclude=company_words)

    # Build resume word set AND bigram set for matching
    resume_words = set(w.lower() for w in _WORD_RE.findall(resume_text))
    resume_bigrams = set(_extract_bigrams(resume_text))

    matched = []
    missing = []
    for kw in jd_top_keywords:
        if " " in kw:
            # Bigram: check against resume bigrams
            if kw in resume_bigrams:
                matched.append(kw)
            else:
                # Fallback: both words present individually?
                parts = kw.split()
                if all(p in resume_words for p in parts):
                    matched.append(kw)
                else:
                    missing.append(kw)
        else:
            # Single word
            if kw in resume_words:
                matched.append(kw)
            else:
                missing.append(kw)

    score = round(100 * len(matched) / max(len(jd_top_keywords), 1))
    return {
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "jd_top_keywords": jd_top_keywords,
    }


def tailor_resume(resume_text: str, jd_text: str, provider: str = "gemini", api_key: str | None = None,
                   model: str | None = None) -> dict:
    """Calls an LLM to produce a structured, JD-tailored resume.
    Returns a dict matching the schema described in prompts.SYSTEM_PROMPT.
    Raises ValueError if the model does not return parseable JSON."""

    if provider.lower() == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=model or "gemini-3.5-flash",
            contents=build_user_prompt(resume_text, jd_text),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        raw_text = response.text.strip()
    else:
        raise ValueError(f"Unknown provider: {provider}. Only 'gemini' is supported.")

    # Defensive cleanup in case the model wraps JSON in a code fence anyway.
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip())

    try:
        parsed = json.loads(raw_text)
        logging.info("JSON parsing succeeded. Keys: %s", list(parsed.keys()))
        return parsed
    except json.JSONDecodeError as exc:
        logging.error("JSON parsing failed. First 300 chars: %s", raw_text[:300])
        raise ValueError(
            f"Model did not return valid JSON. Raw response was:\n{raw_text[:500]}"
        ) from exc
