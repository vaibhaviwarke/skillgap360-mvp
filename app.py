"""SkillGap360 – Skill Passport (Version 1)

One user (an IT-services employee), one problem (no trusted view of my skills vs a
target role), one workflow (evidence → AI draft → employee review → readiness and
passport) and one AI capability (evidence-based skill inference with Gemini).
"""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from skillgap.grounding import check_assessment
from skillgap.inference import DEFAULT_MODEL, InferenceError, infer_skills, load_demo_result
from skillgap.passport import build_passport, to_json, to_markdown
from skillgap.privacy import prepare_text
from skillgap.roles import LEVEL_SHORT, LEVELS, ROLE_TEMPLATES, WEIGHT_LABEL, role_names, role_skills
from skillgap.scoring import readiness, readiness_band, top_gaps

APP_DIR = Path(__file__).resolve().parent
SAMPLE_PROFILE = (APP_DIR / "sample_data" / "sample_profile.txt").read_text(encoding="utf-8")
SHORT_TO_LEVEL = {v: k for k, v in LEVEL_SHORT.items()}

st.set_page_config(page_title="SkillGap360 – Skill Passport", page_icon="🧭", layout="wide")


# ---------- helpers ----------
def secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:  # no secrets file when running locally without one
        return default


def read_upload(upload):
    """Extract text from an uploaded PDF, DOCX or TXT file."""
    data = upload.getvalue()
    name = upload.name.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if name.endswith(".docx"):
        import docx
        document = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs)
    return data.decode("utf-8", errors="ignore")


def build_rows(result, role_name, source_text):
    """Combine the role template, the AI ratings and the grounding check into review rows."""
    by_skill = {a.skill: a for a in result.assessments}
    rows = []
    for s in role_skills(role_name):
        a = by_skill[s["name"]]
        level, status = check_assessment(a.level, a.evidence, source_text)
        rows.append({
            "name": s["name"], "target": s["target"], "weight": s["weight"], "next_step": s["next_step"],
            "ai_level": level, "level": level, "evidence": a.evidence, "reasoning": a.reasoning, "status": status,
        })
    return rows


def reset_results():
    for key in ("result", "rows", "source_text", "is_demo", "editor"):
        st.session_state.pop(key, None)


# Button callbacks run before widgets are drawn, so they may safely change the text box.
def load_sample():
    st.session_state["profile"] = SAMPLE_PROFILE
    reset_results()


def run_demo():
    role_name = st.session_state.get("role", "ML Engineer")
    if role_name != "ML Engineer":
        st.session_state["demo_role_warning"] = True
        return
    reset_results()
    clean, _, _ = prepare_text(SAMPLE_PROFILE)
    st.session_state["profile"] = SAMPLE_PROFILE
    result = load_demo_result(role_name)
    st.session_state.update(result=result, source_text=clean, is_demo=True,
                            rows=build_rows(result, role_name, clean))


# ---------- sidebar ----------
with st.sidebar:
    st.header("About this version")
    st.write(
        "**SkillGap360 Skill Passport (V1)** helps an employee see, with evidence, which skills they "
        "already have for a target internal role and which three gaps to close first."
    )
    st.markdown(
        "**How your data is handled**\n"
        "- Emails, phone numbers and links are removed before anything is sent.\n"
        "- Text is sent once to Google Gemini to draft ratings. Nothing is stored by this app.\n"
        "- AI only suggests. You review and confirm every rating.\n"
        "- Your passport is a file only you download and choose to share."
    )
    st.warning(
        "**Test version on Gemini's free tier.** Google may use free-tier inputs to improve its products, "
        "and human reviewers may read them. Use the sample profile, or remove your name, employer, client "
        "names and any confidential details before pasting."
    )
    with st.expander("Settings"):
        user_key = st.text_input("Your own Gemini API key (optional)", type="password",
                                 help="Used only for this session. Leave blank to use the app's key.")
        model = st.text_input("Model", value=secret("GEMINI_MODEL", DEFAULT_MODEL))
    api_key = user_key or secret("GEMINI_API_KEY")
    st.caption("AI status: " + ("connected" if api_key else "no API key – demo mode only"))
    st.divider()
    st.caption("DPM2026 · Group 02 · Version 1 (MVP)")

# ---------- header ----------
st.title("🧭 SkillGap360 · Skill Passport")
st.write("Turn your CV and project work into an **evidence-backed skill profile**, see how ready you are for a "
         "target internal role, and get the **three gaps to close first**.")

steps = st.columns(4)
for col, (num, label) in zip(steps, [("1", "Add your evidence"), ("2", "AI drafts your skills"),
                                     ("3", "You review and correct"), ("4", "Readiness and passport")]):
    col.markdown(f"**{num}.** {label}")
st.divider()

# ---------- step 1: evidence ----------
st.subheader("1 · Add your evidence")
left, right = st.columns([2, 1])
with right:
    role_name = st.selectbox("Target internal role", role_names(), key="role", on_change=reset_results)
    st.caption(ROLE_TEMPLATES[role_name]["description"])
    with st.expander("Skills this role needs"):
        for s in role_skills(role_name):
            st.markdown(f"- {s['name']} — target {s['target']} · {WEIGHT_LABEL[s['weight']]}")
    st.button("Load sample profile (fictional)", use_container_width=True, on_click=load_sample)
with left:
    upload = st.file_uploader("Upload your CV (PDF, DOCX or TXT) – optional", type=["pdf", "docx", "txt"])
    if upload is not None and st.session_state.get("last_upload") != upload.name:
        try:
            st.session_state["profile"] = read_upload(upload)
            st.session_state["last_upload"] = upload.name
            reset_results()
        except Exception:
            st.error("Could not read that file. Please paste the text instead.")
    profile = st.text_area(
        "Or paste your CV, project descriptions and certifications",
        key="profile", height=260,
        placeholder="e.g. 'Built Spring Boot microservices… Wrote Python scripts to automate… Trained a logistic regression model…'",
    )

consent = st.checkbox("I understand my text (with emails, phone numbers and links removed) is sent to Google Gemini's free tier "
                      "to draft my ratings, that I should not include confidential or personal details, and that I will "
                      "review every rating myself.")

b1, b2 = st.columns([1, 1])
run_live = b1.button("Draft my Skill Passport", type="primary", disabled=not (consent and api_key),
                     use_container_width=True)
b2.button("Show demo with sample AI output", use_container_width=True, on_click=run_demo,
          help="Pre-recorded AI output for the fictional sample profile and the ML Engineer role. "
               "Use if the live AI is unavailable.")
if st.session_state.pop("demo_role_warning", False):
    st.warning("The demo is recorded for the ML Engineer role. Switch the role to ML Engineer and try again.")
if not api_key:
    st.info("No API key configured, so live AI is off. You can still try the labelled demo.")

if run_live:
    clean, counts, truncated = prepare_text(profile)
    with st.spinner("Reading your evidence and drafting ratings…"):
        try:
            result = infer_skills(clean, role_name, api_key=api_key, model=model)
            st.session_state.update(result=result, source_text=clean, is_demo=False,
                                    rows=build_rows(result, role_name, clean))
            removed = sum(counts.values())
            if removed:
                st.success(f"Removed {removed} contact detail(s) before sending.")
            if truncated:
                st.warning("Your text was long, so only the first part was analysed.")
        except InferenceError as err:
            st.error(str(err))


# ---------- step 2 & 3: AI draft + employee review ----------
if "rows" in st.session_state:
    rows = st.session_state["rows"]
    result = st.session_state["result"]
    st.divider()
    st.subheader("2 · AI draft  →  3 · Your review")
    if st.session_state.get("is_demo"):
        st.warning("DEMO – these ratings are pre-recorded AI output for the fictional sample profile, not a live AI call.")
    st.write(result.summary)
    st.caption("The AI drafts; you decide. Change **Your level** wherever the draft is wrong. "
               "⚠️ means the AI's quote could not be found in your text, so the rating was capped at Basic – please check it.")

    status_icon = {"verified": "✅ evidence found", "unverified": "⚠️ check this", "none": "– no evidence"}
    table = pd.DataFrame([{
        "Skill": r["name"],
        "Importance": WEIGHT_LABEL[r["weight"]],
        "Target": LEVEL_SHORT[r["target"]],
        "AI level": LEVEL_SHORT[r["ai_level"]],
        "Your level": LEVEL_SHORT[r["level"]],
        "Check": status_icon[r["status"]],
        "Evidence from your text": " | ".join(f"“{e}”" for e in r["evidence"]) or "–",
    } for r in rows])

    edited = st.data_editor(
        table, key="editor", hide_index=True, use_container_width=True,
        disabled=["Skill", "Importance", "Target", "AI level", "Evidence from your text", "Check"],
        column_config={
            "Your level": st.column_config.SelectboxColumn("Your level ✏️", options=list(LEVEL_SHORT.values()), required=True),
            "Evidence from your text": st.column_config.TextColumn(width="large"),
        },
    )
    for r, value in zip(rows, edited["Your level"]):
        r["level"] = SHORT_TO_LEVEL[value]

    changed = sum(1 for r in rows if r["level"] != r["ai_level"])
    st.caption(f"You changed {changed} of {len(rows)} AI ratings.")
    with st.expander("Rating scale and AI reasoning"):
        for k, v in LEVELS.items():
            st.markdown(f"- **{k}** – {v}")
        st.markdown("---")
        for r in rows:
            st.markdown(f"- **{r['name']}**: {r['reasoning']}")
    if result.other_skills:
        with st.expander(f"Other skills the AI found ({len(result.other_skills)})"):
            for o in result.other_skills:
                st.markdown(f"- **{o.skill}** – “{o.evidence}”")

    # ---------- step 4: readiness + passport ----------
    st.divider()
    st.subheader("4 · Your readiness and Skill Passport")
    score = readiness(rows)
    gaps = top_gaps(rows)
    m1, m2 = st.columns([1, 2])
    m1.metric(f"Readiness for {role_name}", f"{score}%")
    m1.caption(readiness_band(score))
    progress = pd.DataFrame([{
        "Skill": r["name"], "Importance": WEIGHT_LABEL[r["weight"]],
        "Progress to target": min(r["level"] / r["target"], 1.0) * 100,
        "Level": f"{r['level']} / {r['target']}",
    } for r in rows])
    m2.dataframe(progress, hide_index=True, use_container_width=True, column_config={
        "Progress to target": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
    })

    st.markdown("#### Your top 3 gaps to close first")
    if not gaps:
        st.success("No gaps against this role's targets. Consider applying.")
    for i, (col, g) in enumerate(zip(st.columns(max(len(gaps), 1)), gaps), 1):
        with col.container(border=True):
            st.markdown(f"**{i}. {g['name']}**")
            st.caption(f"{WEIGHT_LABEL[g['weight']]} · level {g['level']} → {g['target']}")
            st.write(g["next_step"])

    st.markdown("#### Save your Skill Passport")
    confirmed = st.checkbox("I have reviewed these ratings and they reflect my skills.")
    other = [{"skill": o.skill, "evidence": o.evidence} for o in result.other_skills]
    passport = build_passport(role_name, rows, other, score, gaps, confirmed)
    d1, d2 = st.columns(2)
    d1.download_button("Download passport (JSON – for systems)", to_json(passport),
                       file_name="skill_passport.json", mime="application/json",
                       disabled=not confirmed, use_container_width=True)
    d2.download_button("Download passport (Markdown – for people)", to_markdown(passport),
                       file_name="skill_passport.md", mime="text/markdown",
                       disabled=not confirmed, use_container_width=True)
    st.caption("Coming next (V2): share your confirmed passport with your manager or resource team "
               "so you're considered for projects that match your skills.")
