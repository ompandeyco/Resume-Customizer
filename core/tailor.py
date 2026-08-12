"""
Core AI logic:
1. tailor_resume()      -> calls Claude to produce a structured, JD-tailored
                            resume (JSON) from raw resume text + JD text.
2. keyword_match_score() -> a cheap, deterministic (non-LLM) ATS-style
                            keyword overlap score, used to show a concrete
                            "before vs after" improvement number in the UI.
"""

import json
import os
import re
from collections import Counter

import anthropic

from core.prompts import SYSTEM_PROMPT, build_user_prompt

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

# A small stopword list is enough for a keyword-overlap heuristic; we don't
# need a full NLP stack for this.
_STOPWORDS = set("""
a an the and or but if then else for of to in on at by with from as is are
was were be been being this that these those it its it's you your our we
they their he she his her i my me will would can could should shall may
might must not no yes do does did doing have has had having up down out
over under again further once here there all any both each few more most
other some such only own same so than too very s t just don don't now
""".split())

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.#-]{1,}")


def _keywords(text: str, top_n: int = 40) -> Counter:
    words = [w.lower() for w in _WORD_RE.findall(text)]
    words = [w for w in words if w not in _STOPWORDS and len(w) > 2]
    return Counter(words).most_common(top_n)


def keyword_match_score(resume_text: str, jd_text: str) -> dict:
    """Returns overlap between the JD's top keywords and the resume text.
    This is a simple heuristic (not the LLM) so the score is fast, free,
    and deterministic -- useful as a concrete before/after metric."""
    jd_top_keywords = [w for w, _ in _keywords(jd_text, top_n=30)]
    resume_words = set(w.lower() for w in _WORD_RE.findall(resume_text))

    matched = [w for w in jd_top_keywords if w in resume_words]
    missing = [w for w in jd_top_keywords if w not in resume_words]

    score = round(100 * len(matched) / max(len(jd_top_keywords), 1))
    return {
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "jd_top_keywords": jd_top_keywords,
    }


def tailor_resume(resume_text: str, jd_text: str, api_key: str | None = None,
                   model: str = DEFAULT_MODEL) -> dict:
    """Calls Claude to produce a structured, JD-tailored resume.
    Returns a dict matching the schema described in prompts.SYSTEM_PROMPT.
    Raises ValueError if the model does not return parseable JSON."""

    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=model,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_user_prompt(resume_text, jd_text)}
        ],
    )

    raw_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ).strip()

    # Defensive cleanup in case the model wraps JSON in a code fence anyway.
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip())

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model did not return valid JSON. Raw response was:\n{raw_text[:500]}"
        ) from exc
