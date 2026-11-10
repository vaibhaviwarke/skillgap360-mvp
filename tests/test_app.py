"""End-to-end UI test with Streamlit's AppTest (no real AI call: uses the labelled demo path)."""

from streamlit.testing.v1 import AppTest


def _button(at, label):
    return next(b for b in at.button if b.label.startswith(label))


def test_demo_workflow_end_to_end():
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert not at.exception
    _button(at, "Load sample profile").click().run()
    assert "Spring Boot" in at.text_area[0].value
    _button(at, "Show demo").click().run()
    assert not at.exception
    assert any("DEMO" in w.value for w in at.warning)
    readiness = at.metric[0]
    assert readiness.label.startswith("Readiness for ML Engineer")
    assert readiness.value.endswith("%")
    # live button is disabled without consent / key
    assert _button(at, "Draft my Skill Passport").disabled
    # downloads unlock only after the employee confirms
    at.checkbox[-1].check().run()
    assert not at.exception
