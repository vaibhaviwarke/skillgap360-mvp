"""The one AI capability: evidence-based skill inference with Google Gemini.

Input : the employee's own CV / project text (contact details already removed)
        + the skill list for the target role they chose.
AI    : rates each listed skill 0-4 against a fixed rubric and quotes the exact
        sentence it relied on. It must not guess from job titles, names or demographics.
Output: structured JSON (validated with Pydantic) that the app turns into an
        editable review table, a readiness score and a portable Skill Passport.
"""

import json
import time
from pathlib import Path

from pydantic import BaseModel, Field

from .roles import LEVELS, role_skills

DEFAULT_MODEL = "gemini-flash-latest"


class SkillAssessment(BaseModel):
    skill: str = Field(description="Exactly one of the skill names provided, copied verbatim.")
    level: int = Field(description="Proficiency 0-4 using the rubric.")
    evidence: list[str] = Field(description="Up to 2 short quotes copied word-for-word from the employee text. Empty if level is 0.")
    reasoning: str = Field(description="One short sentence explaining the rating.")


class OtherSkill(BaseModel):
    skill: str
    evidence: str = Field(description="A short quote copied word-for-word from the employee text.")


class InferenceResult(BaseModel):
    assessments: list[SkillAssessment]
    other_skills: list[OtherSkill] = Field(description="Up to 5 notable skills not in the list, with evidence.")
    summary: str = Field(description="Two sentences: strongest evidence-backed skills, and what evidence is missing.")


class InferenceError(Exception):
    """Raised with a message that is safe to show to the user."""


def build_instructions():
    rubric = "\n".join(f"{k} = {v}" for k, v in LEVELS.items())
    return f"""You are a careful, fair skills assessor helping an employee build their own Skill Passport.

Rate each listed skill using ONLY evidence in the employee's text.

Proficiency rubric:
{rubric}

Rules:
1. Every rating above 0 must be backed by 1-2 quotes copied word-for-word from the text (max 25 words each). Never paraphrase inside a quote.
2. If there is no evidence for a skill, give level 0 and an empty evidence list. Do not guess.
3. A job title, course name or certificate alone is at most level 1. Level 2+ needs evidence of real project use.
4. Credit transferable evidence only when the text shows it directly (e.g. Docker used for Java services counts toward containers).
5. Ignore names, gender, age, nationality, career breaks and any personal details. Rate skills, not people.
6. Be conservative: when unsure between two levels, choose the lower one. Employees will review and can raise it.
7. Return every listed skill exactly once, in the order given, using the exact skill name."""


def build_prompt(profile_text, role_name):
    skills = "\n".join(f"- {s['name']}" for s in role_skills(role_name))
    return f"""Target role: {role_name}

Skills to assess (in this order):
{skills}

Employee text (contact details removed):
\"\"\"
{profile_text}
\"\"\""""


def _make_client(api_key):
    from google import genai  # imported here so the rest of the app (and tests) work without the SDK
    return genai.Client(api_key=api_key)


def _config():
    from google.genai import types
    return types.GenerateContentConfig(
        system_instruction=build_instructions(),
        response_mime_type="application/json",
        response_schema=InferenceResult,
        temperature=0.1,
    )


def _parse(response):
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, InferenceResult):
        return parsed
    text = getattr(response, "text", None)
    if not text:
        raise InferenceError("The AI returned an empty answer. Please try again.")
    try:
        return InferenceResult.model_validate_json(text)
    except Exception as exc:
        raise InferenceError("The AI answer was not in the expected format. Please try again.") from exc


def normalise(result, role_name):
    """Make the AI output safe to use: known skills only, levels clamped, one row per skill."""
    by_name = {a.skill.strip().lower(): a for a in result.assessments}
    fixed = []
    for s in role_skills(role_name):
        a = by_name.get(s["name"].lower())
        if a is None:
            fixed.append(SkillAssessment(skill=s["name"], level=0, evidence=[], reasoning="No assessment returned."))
        else:
            fixed.append(SkillAssessment(
                skill=s["name"],
                level=max(0, min(4, int(a.level))),
                evidence=[e.strip() for e in a.evidence if e and e.strip()][:2],
                reasoning=a.reasoning.strip(),
            ))
    return InferenceResult(assessments=fixed, other_skills=result.other_skills[:5], summary=result.summary.strip())


def infer_skills(profile_text, role_name, api_key, model=DEFAULT_MODEL, client=None, retries=1):
    """Call Gemini once and return a normalised InferenceResult. `client` can be injected for tests."""
    if not profile_text or len(profile_text.split()) < 30:
        raise InferenceError("Please add more detail – at least a short CV or a few project descriptions (30+ words).")
    if client is None:
        if not api_key:
            raise InferenceError("No Gemini API key is configured.")
        client = _make_client(api_key)

    last_error = None
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=model, contents=build_prompt(profile_text, role_name), config=_config(),
            )
            return normalise(_parse(response), role_name)
        except InferenceError:
            raise
        except Exception as exc:  # network, quota, model name, safety block
            last_error = exc
            msg = str(exc)
            if attempt < retries and any(code in msg for code in ("429", "500", "503", "UNAVAILABLE", "RESOURCE_EXHAUSTED")):
                time.sleep(2)
                continue
            break

    msg = str(last_error)
    if "API key" in msg or "PERMISSION_DENIED" in msg or "401" in msg or "403" in msg:
        raise InferenceError("The Gemini API key was rejected. Check the key in the app settings.") from last_error
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        raise InferenceError("The free Gemini quota is used up for now. Wait a minute and try again, or use the demo.") from last_error
    if "404" in msg or "NOT_FOUND" in msg:
        raise InferenceError(f"The model '{model}' is not available. Set GEMINI_MODEL in secrets to a current model.") from last_error
    raise InferenceError("Could not reach the AI service. Please try again in a moment.") from last_error


def load_demo_result(role_name, sample_dir=None):
    """Pre-recorded AI output for the built-in sample profile, used only in clearly labelled demo mode."""
    sample_dir = Path(sample_dir or Path(__file__).resolve().parent.parent / "sample_data")
    data = json.loads((sample_dir / "demo_ai_output.json").read_text(encoding="utf-8"))
    if role_name not in data:
        raise InferenceError("Demo output is only available for the ML Engineer role with the sample profile.")
    return normalise(InferenceResult.model_validate(data[role_name]), role_name)
