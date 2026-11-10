"""Grounding check: is each AI evidence quote really in the employee's own text?

This is a deterministic guardrail against hallucination. If the AI claims a skill
but its quote cannot be found in the input, the rating is capped and flagged for
the employee to verify. (Interview I3: "it has to be accurate before it's clever".)
"""

import re

_WORD = re.compile(r"[a-z0-9+#.]+")


def _tokens(text):
    return [t.strip(".") for t in _WORD.findall(text.lower()) if len(t.strip(".")) >= 3]


def quote_is_grounded(quote, source, threshold=0.8):
    """True if the quote appears verbatim, or at least `threshold` of its words appear in the source."""
    if not quote or not quote.strip():
        return False
    norm = lambda s: re.sub(r"\s+", " ", s.lower()).strip()
    if norm(quote) in norm(source):
        return True
    q = _tokens(quote)
    if not q:
        return False
    src = set(_tokens(source))
    hits = sum(1 for t in q if t in src)
    return hits / len(q) >= threshold


def check_assessment(level, evidence, source):
    """Return (adjusted_level, status). Status is 'verified', 'unverified' or 'none'."""
    grounded = [e for e in (evidence or []) if quote_is_grounded(e, source)]
    if level <= 0:
        return 0, "none"
    if grounded:
        return level, "verified"
    # Claimed a skill without findable evidence: keep it visible but capped at Basic.
    return min(level, 1), "unverified"
