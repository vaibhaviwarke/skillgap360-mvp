"""Build the employee-owned Skill Passport (JSON for systems, Markdown for people).

The JSON uses a simple, documented schema so a later version can plug the passport
into staffing / resource-allocation tools without re-assessing the employee.
"""

import json
from datetime import datetime, timezone

from .roles import LEVELS, WEIGHT_LABEL

SCHEMA = "skillgap360.passport/v1"


def build_passport(role_name, rows, other_skills, score, gaps, confirmed):
    return {
        "schema": SCHEMA,
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "owner": "employee",
        "sharing": "Not shared. Only the employee can choose to share this file.",
        "employee_confirmed": bool(confirmed),
        "target_role": role_name,
        "role_readiness_pct": score,
        "skills": [
            {
                "skill": r["name"],
                "level": r["level"],
                "level_label": LEVELS[r["level"]],
                "target_level": r["target"],
                "importance": WEIGHT_LABEL[r["weight"]],
                "source": "employee-edited" if r["level"] != r["ai_level"] else "ai-suggested, employee-reviewed",
                "evidence": r["evidence"],
                "evidence_check": r["status"],
            }
            for r in rows
        ],
        "other_skills": [{"skill": o["skill"], "evidence": o["evidence"]} for o in other_skills],
        "priority_gaps": [
            {"skill": g["name"], "current": g["level"], "target": g["target"], "next_step": g["next_step"]}
            for g in gaps
        ],
    }


def to_json(passport):
    return json.dumps(passport, indent=2, ensure_ascii=False)


def to_markdown(passport):
    lines = [
        f"# Skill Passport – target role: {passport['target_role']}",
        "",
        f"Role readiness: **{passport['role_readiness_pct']}%**  ",
        f"Confirmed by employee: {'yes' if passport['employee_confirmed'] else 'not yet'}  ",
        f"Created: {passport['created_utc']}",
        "",
        "## Skills",
        "",
        "| Skill | Level | Target | Evidence |",
        "|---|---|---|---|",
    ]
    for s in passport["skills"]:
        ev = "; ".join(f"“{e}”" for e in s["evidence"]) or "–"
        lines.append(f"| {s['skill']} | {s['level']} | {s['target_level']} | {ev} |")
    lines += ["", "## Priority gaps and next steps", ""]
    for i, g in enumerate(passport["priority_gaps"], 1):
        lines.append(f"{i}. **{g['skill']}** (level {g['current']} → {g['target']}): {g['next_step']}")
    if passport["other_skills"]:
        lines += ["", "## Other skills found", ""]
        lines += [f"- {o['skill']} – “{o['evidence']}”" for o in passport["other_skills"]]
    lines += ["", "_Employee-owned record. Ratings were drafted by AI from the employee's own text and reviewed by the employee._"]
    return "\n".join(lines)
