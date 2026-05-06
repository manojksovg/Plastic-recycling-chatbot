"""
matcher.py
Intent detection and keyword-matching logic.
Includes whole-word matching and ambiguous-word protection
to prevent e.g. "can I recycle" matching the metal-can rule.
"""

import re

# Single words that appear in item keyword lists but are also
# common English words. They only score points when paired with
# at least one other multi-word keyword match from the same rule.
AMBIGUOUS_SINGLE_WORDS = {
    "can", "tin", "film", "cup", "cap", "box", "bag", "tray",
    "glass", "card", "wrap", "oil", "cable", "clear",
}

# Add "bottle" to the rule keywords at match time via a normalisation step
# These tokens are specific enough to score even as single words
STRONG_SINGLE_WORDS = {
    "paper", "bottle", "straw", "cutlery", "battery", "styrofoam",
    "polystyrene", "foam", "tissue", "napkin", "cardboard", "carton",
}

REPORT_KEYWORDS = {"full", "overflow", "broken", "damage", "block",
                   "contamination", "missing", "issue", "problem",
                   "stuck", "leak", "report"}

FAQ_KEYWORDS = {"what is", "why", "how", "policy", "rule", "should i",
                "when", "who", "purpose", "difference", "explain"}


def detect_intent(text: str) -> str:
    """
    Returns one of: 'disposal' | 'faq' | 'report'
    """
    t = text.lower()
    words = set(t.split())

    # Report: bin-related problem keywords
    if REPORT_KEYWORDS & words and ("bin" in t or "report" in t or "issue" in t):
        return "report"

    # FAQ: question/policy phrasing
    if any(kw in t for kw in FAQ_KEYWORDS):
        return "faq"

    return "disposal"


def _score(text: str, keyword_str: str) -> int:
    """
    Score a user query against a semicolon-separated keyword string.
    Uses whole-word regex matching and penalises ambiguous single words.
    """
    t_norm = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    t_norm = re.sub(r"\s+", " ", t_norm).strip()

    keywords = [k.strip().lower() for k in keyword_str.split(";") if k.strip()]
    score = 0

    for kw in keywords:
        escaped = re.escape(kw)
        pattern = re.compile(r"(?:^|\s)" + escaped + r"(?:\s|$)")
        if pattern.search(t_norm):
            word_count = len(kw.split())
            if word_count == 1 and kw in AMBIGUOUS_SINGLE_WORDS:
                # Ambiguous single word — too likely to be a false positive
                pass
            elif word_count == 1 and kw in STRONG_SINGLE_WORDS:
                # Specific enough to count on its own, but score lower than phrases
                score += 2
            else:
                score += word_count * 2  # multi-word phrases score highest

    return score


def find_best_rule(text: str, rules: list[dict]) -> dict | None:
    """Return the best-matching disposal rule, or None if no good match."""
    best, best_score = None, 0
    for rule in rules:
        s = _score(text, rule["keywords"])
        if s > best_score:
            best_score = s
            best = rule
    # Require a minimum score of 2 to avoid spurious single-word matches
    return best if best_score >= 2 else None


def find_best_faq(text: str, faqs: list[dict]) -> dict | None:
    """Return the best-matching FAQ entry, or None."""
    best, best_score = None, 0
    for faq in faqs:
        s = _score(text, faq["keywords"])
        if s > best_score:
            best_score = s
            best = faq
    return best if best_score >= 2 else None
