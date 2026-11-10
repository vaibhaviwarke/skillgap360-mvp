"""Role readiness and gap ranking. Plain arithmetic, so results are explainable and repeatable."""


def readiness(rows):
    """Weighted % of target proficiency reached. rows: dicts with level, target, weight."""
    total = sum(r["weight"] for r in rows)
    if total == 0:
        return 0
    reached = sum(r["weight"] * min(r["level"] / r["target"], 1.0) for r in rows if r["target"] > 0)
    return round(100 * reached / total)


def top_gaps(rows, n=3):
    """Rank skills below target by weight × levels missing; ties go to the more important skill."""
    gaps = []
    for r in rows:
        missing = max(r["target"] - r["level"], 0)
        if missing > 0:
            gaps.append({**r, "missing": missing, "priority": r["weight"] * missing})
    gaps.sort(key=lambda g: (-g["priority"], -g["weight"], g["name"]))
    return gaps[:n]


def readiness_band(score):
    if score >= 80:
        return "Ready to apply"
    if score >= 60:
        return "Close – a focused 90-day plan should get you there"
    if score >= 40:
        return "Building – several important gaps to close"
    return "Early – start with the critical skills"
