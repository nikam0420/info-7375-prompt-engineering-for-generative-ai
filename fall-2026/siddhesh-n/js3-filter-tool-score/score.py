"""Deterministic filter and narrowly scoped textual evidence."""
import re

TITLE_WEIGHT = 3
BODY_WEIGHT = 1
THRESHOLD = 4
ROLE = re.compile(
    r"\b(?:data analysts?|business intelligence|analytics engineers?|"
    r"data engineers?|business analysts?)\b", re.I
)
SIGNALS = {
    "SQL": r"\bSQL\b",
    "dashboards": r"\bdashboards?\b",
    "ETL": r"\bETL\b",
    "data pipelines": r"\bdata pipelines?\b",
    "data modeling": r"\bdata model(?:l)?ing\b",
    "reporting": r"\breporting\b",
}

def score(title, text, threshold=THRESHOLD):
    if not title or not title.strip() or not text or not text.strip():
        return {"decision": "unknown", "score": None,
                "reason": "I cannot tell without the title and posting text."}
    title_match = ROLE.search(title)
    evidence = {}
    for signal, pattern in SIGNALS.items():
        match = re.search(pattern, text, re.I)
        if match:
            evidence[signal] = match.group()
    points = TITLE_WEIGHT * bool(title_match) + BODY_WEIGHT * len(evidence)
    return {
        "decision": "keep" if points >= threshold else "reject",
        "score": points, "title_match": title_match.group() if title_match else None,
        "mentions": evidence,
    }
