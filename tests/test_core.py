import json
from types import SimpleNamespace

import pytest

from skillgap.grounding import check_assessment, quote_is_grounded
from skillgap.inference import InferenceError, InferenceResult, infer_skills, load_demo_result
from skillgap.passport import build_passport, to_json, to_markdown
from skillgap.privacy import prepare_text, redact
from skillgap.roles import ROLE_TEMPLATES, role_skills
from skillgap.scoring import readiness, top_gaps

SAMPLE = open("sample_data/sample_profile.txt", encoding="utf-8").read()


def test_redact_removes_contact_details_but_keeps_years():
    text = "Mail priya.sample@example.com, call +91 98765 43210, see linkedin.com/in/x. Joined 2022, 4 years."
    out, counts = redact(text)
    assert "example.com" not in out and "98765" not in out and "linkedin" not in out
    assert "2022" in out and "4 years" in out
    assert counts == {"emails": 1, "links": 1, "phones": 1}


def test_prepare_text_caps_length():
    clean, _, truncated = prepare_text("word " * 5000)
    assert truncated and len(clean) <= 12000


def test_grounding_accepts_real_quote_and_rejects_invented_one():
    assert quote_is_grounded("trained a logistic regression model in scikit-learn", SAMPLE)
    assert not quote_is_grounded("Deployed TensorFlow models on Kubernetes at scale", SAMPLE)


def test_unverified_claim_is_capped_at_basic():
    assert check_assessment(3, ["Built PyTorch transformers for NLP"], SAMPLE) == (1, "unverified")
    assert check_assessment(3, ["Led code reviews for a team of five engineers"], SAMPLE) == (3, "verified")
    assert check_assessment(0, [], SAMPLE) == (0, "none")


def test_readiness_and_gap_ranking():
    rows = [
        {"name": "A", "target": 3, "weight": 3, "level": 3},
        {"name": "B", "target": 2, "weight": 3, "level": 0},
        {"name": "C", "target": 2, "weight": 1, "level": 0},
        {"name": "D", "target": 3, "weight": 2, "level": 2},
    ]
    # reached = 3*1 + 0 + 0 + 2*(2/3) = 4.333 of 9 -> 48%
    assert readiness(rows) == 48
    assert [g["name"] for g in top_gaps(rows)] == ["B", "C", "D"] or [g["name"] for g in top_gaps(rows)] == ["B", "D", "C"]
    assert top_gaps(rows)[0]["name"] == "B"


def test_all_role_templates_are_valid():
    for role, tpl in ROLE_TEMPLATES.items():
        assert len(tpl["skills"]) == 8, role
        for s in tpl["skills"]:
            assert 1 <= s["target"] <= 4 and s["weight"] in (1, 2, 3) and s["next_step"]


def test_demo_output_quotes_are_all_grounded():
    clean, _, _ = prepare_text(SAMPLE)
    result = load_demo_result("ML Engineer")
    for a in result.assessments:
        for e in a.evidence:
            assert quote_is_grounded(e, clean), e


class FakeModels:
    def __init__(self, payload, fail_times=0, error="503 UNAVAILABLE"):
        self.payload, self.fail_times, self.error, self.calls = payload, fail_times, error, 0

    def generate_content(self, model, contents, config):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(self.error)
        assert "Python programming" in contents and "[EMAIL]" in contents
        return SimpleNamespace(parsed=None, text=json.dumps(self.payload))


def _payload():
    data = json.load(open("sample_data/demo_ai_output.json"))["ML Engineer"]
    data["assessments"] = data["assessments"][:-1]  # AI forgot one skill
    data["assessments"][0]["level"] = 9  # out-of-range level
    data["assessments"].append({"skill": "Juggling", "level": 4, "evidence": [], "reasoning": "x"})  # unknown skill
    return data


def test_infer_skills_normalises_bad_ai_output_and_retries():
    clean, _, _ = prepare_text(SAMPLE)
    fake = FakeModels(_payload(), fail_times=1)
    result = infer_skills(clean, "ML Engineer", api_key=None, client=SimpleNamespace(models=fake), retries=1)
    names = [a.skill for a in result.assessments]
    assert names == [s["name"] for s in role_skills("ML Engineer")]
    assert result.assessments[0].level == 4  # clamped from 9
    assert result.assessments[-1].level == 0  # missing skill filled with 0
    assert fake.calls == 2


def test_infer_skills_gives_friendly_quota_message():
    clean, _, _ = prepare_text(SAMPLE)
    fake = FakeModels(_payload(), fail_times=5, error="429 RESOURCE_EXHAUSTED")
    with pytest.raises(InferenceError, match="quota"):
        infer_skills(clean, "ML Engineer", api_key=None, client=SimpleNamespace(models=fake), retries=1)


def test_short_input_is_rejected_before_any_ai_call():
    with pytest.raises(InferenceError, match="more detail"):
        infer_skills("Java developer", "ML Engineer", api_key="x")


def test_passport_exports():
    rows = [{"name": s["name"], "target": s["target"], "weight": s["weight"], "next_step": s["next_step"],
             "level": 1, "ai_level": 2, "evidence": ["x"], "status": "verified"} for s in role_skills("Data Engineer")]
    p = build_passport("Data Engineer", rows, [], readiness(rows), top_gaps(rows), True)
    assert json.loads(to_json(p))["schema"] == "skillgap360.passport/v1"
    assert p["skills"][0]["source"] == "employee-edited"
    assert "Priority gaps" in to_markdown(p)
