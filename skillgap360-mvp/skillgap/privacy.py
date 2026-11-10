"""Privacy helpers: remove direct contact details before any text leaves the app."""

import re

MAX_CHARS = 12000  # keeps the request small and cheap; a CV plus project notes fits easily

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_URL = re.compile(r"(?:https?://|www\.)\S+|\blinkedin\.com/\S+", re.IGNORECASE)
# Phone numbers: optional country code, then 10+ digits possibly split by spaces, dots or dashes.
_PHONE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?){2,4}\d{3,5}(?!\w)")


def redact(text):
    """Return (redacted_text, counts). Emails, links and phone numbers are replaced with tags."""
    counts = {"emails": 0, "links": 0, "phones": 0}

    def _sub(pattern, tag, key, value):
        def repl(_match):
            counts[key] += 1
            return tag
        return pattern.sub(repl, value)

    out = _sub(_EMAIL, "[EMAIL]", "emails", text)
    out = _sub(_URL, "[LINK]", "links", out)

    def phone_repl(match):
        digits = re.sub(r"\D", "", match.group(0))
        if len(digits) >= 10:  # avoid touching years, version numbers or durations
            counts["phones"] += 1
            return "[PHONE]"
        return match.group(0)

    out = _PHONE.sub(phone_repl, out)
    return out, counts


def prepare_text(text):
    """Redact, normalise whitespace and cap length. Returns (clean_text, counts, truncated)."""
    clean, counts = redact(text or "")
    clean = re.sub(r"[ \t]+", " ", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
    truncated = len(clean) > MAX_CHARS
    return clean[:MAX_CHARS], counts, truncated
