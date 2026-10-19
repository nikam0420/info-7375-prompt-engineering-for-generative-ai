"""Deterministic relevance record (CONTRACT.md, "Relevance rule").

A posting is relevant only when all three conditions hold:
 1. posting.title contains a phrase from résumé.target_titles (case-insensitive substring);
 2. posting.content (HTML -> plain text, entities decoded) contains SQL as a whole word;
 3. résumé.skills has an item equal to SQL (trimmed, case-insensitive).

The same rule is used for hand labels. Expects a posting normalized by
postings.parse_response, whose `content` is already plain text.
"""

from __future__ import annotations

import json
import re

SQL_WORD_RE = re.compile(r"\bsql\b", re.IGNORECASE)
SNIPPET_RADIUS = 40


def title_matches(title: str, target_titles: list[str]) -> list[str]:
    lowered = title.lower()
    return [phrase for phrase in target_titles if phrase.lower() in lowered]


def find_sql(content_text: str):
    return SQL_WORD_RE.search(content_text)


def skill_sql_items(skills: list[str]) -> list[str]:
    return [s for s in skills if s.strip().lower() == "sql"]


def _snippet(text: str, match) -> str:
    start = max(0, match.start() - SNIPPET_RADIUS)
    end = min(len(text), match.end() + SNIPPET_RADIUS)
    snippet = re.sub(r"\s+", " ", text[start:end]).strip()
    return ("…" if start > 0 else "") + snippet + ("…" if end < len(text) else "")


def evaluate(resume: dict, posting: dict) -> dict:
    title = posting["title"]
    content = posting["content"]
    targets = resume["target_titles"]

    matched = title_matches(title, targets)
    sql_match = find_sql(content)
    skill_items = skill_sql_items(resume["skills"])

    c1, c2, c3 = bool(matched), sql_match is not None, bool(skill_items)
    verdict = "relevant" if (c1 and c2 and c3) else "not_relevant"

    if c1:
        j1 = (
            f"Condition 1 (title) passed: posting.title {json.dumps(title)} contains "
            f"résumé.target_titles phrase {json.dumps(matched[0])} (case-insensitive substring)."
        )
    else:
        j1 = (
            f"Condition 1 (title) failed: posting.title {json.dumps(title)} contains none of "
            f"résumé.target_titles {json.dumps(targets)} (case-insensitive substring)."
        )
    if c2:
        j2 = (
            "Condition 2 (SQL in description) passed: posting.content, converted from HTML to "
            "plain text with entities decoded, contains SQL as a whole word: "
            f"{json.dumps(_snippet(content, sql_match), ensure_ascii=False)}."
        )
    else:
        j2 = (
            "Condition 2 (SQL in description) failed: SQL as a whole word is absent from "
            "posting.content after HTML-to-text conversion and entity decoding."
        )
    if c3:
        j3 = (
            f"Condition 3 (SQL skill) passed: résumé.skills contains {json.dumps(skill_items[0])}, "
            "equal to SQL after trimming whitespace (case-insensitive)."
        )
    else:
        j3 = (
            "Condition 3 (SQL skill) failed: résumé.skills has no item equal to SQL after "
            "trimming whitespace (case-insensitive)."
        )

    return {
        "kind": "record",
        "posting_id": posting["id"],
        "verdict": verdict,
        "conditions": {
            "title_contains_target_title": {"passed": c1, "matched_phrases": matched},
            "content_contains_sql_word": {"passed": c2, "match_offset": sql_match.start() if c2 else None},
            "resume_skills_contains_sql": {"passed": c3},
        },
        "resume_fields": ["target_titles", "skills"],
        "posting_fields": ["title", "content"],
        "justification": " ".join([j1, j2, j3]),
    }
