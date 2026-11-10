# SkillGap360 · Skill Passport (Version 1)

**DPM2026 · Group 02** – Prerna Nayyar, Ankit Kharbanda, Vaibhavi Deepak Warke, Sudip Barat, Satish Chandra Rao Damera

**Live app:** https://skillgap360-passport.streamlit.app  *(update this if your Streamlit URL is different)*

---

## What it does

An employee pastes their CV and project notes, picks a target internal role, and gets an **evidence-backed skill profile** drafted by AI. They review and correct every rating, then see:

- how ready they are for the role (weighted readiness %)
- the **three gaps to close first**, each with a concrete next step
- a downloadable **Skill Passport** they own (JSON for systems, Markdown for people)

## Why this, and why first

Our Phase 1 proposal covered employees, managers, L&D and CHROs. The instructor's feedback: address the gap that matters most first – the employee skill passport, because none of the other actors can reach their goals without trusted employee skill data. V1 is therefore:

| One… | V1 |
|---|---|
| Target user | A mid-career IT-services employee aiming for a new internal role |
| Problem | No evidence-based view of my skills against a target role |
| Use case | Check my readiness before applying internally |
| Workflow | Add evidence → AI drafts ratings → employee reviews → readiness and passport |
| AI capability | Evidence-based skill inference with Google Gemini |

## How the AI capability works

1. **Input:** the employee's own text (CV and/or project notes) plus the 8 skills of the chosen role. Emails, phone numbers and links are removed before anything is sent.
2. **AI processing:** one Gemini call (`gemini-flash-latest`, temperature 0.1) rates each skill 0–4 on a fixed rubric. Every rating above 0 must quote the employee's own words. The model is told to ignore names, dates, career breaks and other personal details, and to choose the lower level when unsure. The answer must match a JSON schema (validated with Pydantic).
3. **Guardrails after the call:** unknown skills are dropped and missing ones set to 0; a **grounding check** caps any rating whose quote can't be found in the employee's text and flags it ⚠️.
4. **Output:** an editable review table, a readiness score and the top-3 gaps, all computed with plain arithmetic (no second AI call).

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then paste your Gemini key
streamlit run app.py
```

Get a free Gemini API key at https://aistudio.google.com. Without a key the app still runs, with a clearly labelled demo based on pre-recorded AI output for the fictional sample profile.

## Deploy to Streamlit Community Cloud

1. Push this folder to a **public GitHub repository** (the real `secrets.toml` is git-ignored – never commit your key).
2. Go to https://share.streamlit.io → **Create app** → pick the repo, branch `main`, main file `app.py`.
3. Under **Advanced settings**, choose Python 3.11 or newer and paste into **Secrets**:
   ```toml
   GEMINI_API_KEY = "your-key"
   ```
4. Set the app URL to `skillgap360-passport` (or update the link in this README and the deck).
5. Click **Deploy**, then test the full workflow with the sample profile.

If the default model alias stops working, add `GEMINI_MODEL = "<current model name>"` to Secrets.

## Tests

```bash
python -m pytest -q
```

12 tests cover redaction, the grounding check, readiness and gap maths, role templates, AI-output normalisation (with a fake Gemini client), retry and error messages, passport export, and an end-to-end UI run with Streamlit's `AppTest`.

## Project structure

```
app.py                     Streamlit UI and the 4-step workflow
skillgap/roles.py          Role templates, proficiency rubric, next-step suggestions
skillgap/privacy.py        Redaction of contact details, input cap
skillgap/inference.py      Gemini call, prompt, JSON schema, error handling, demo loader
skillgap/grounding.py      Checks AI quotes against the employee's text
skillgap/scoring.py        Readiness % and top-gap ranking
skillgap/passport.py       Passport export (JSON schema skillgap360.passport/v1, Markdown)
sample_data/               Fictional sample profile and pre-recorded demo output
tests/                     Unit and UI tests
```

## Privacy

- No login, no database: nothing is stored by the app.
- The employee consents before any AI call and confirms every rating.
- **Free-tier notice:** Google's Gemini API terms say that on unpaid services, submitted content may be used to improve Google products, human reviewers may read it, and users should not submit sensitive, confidential or personal information. The app warns users and offers a sample profile. A production version would use the paid tier.

## Limitations

- Three role templates only; skills and targets were set by the team, not validated with employers.
- Ratings depend on how well the employee describes their work.
- Next steps point to well-known free resources; there is no learning content in the app.

## AI-use disclosure

- **Claude (Anthropic)** generated most of this code and the tests. The group reviewed, ran, debugged and deployed it. *(Edit to describe what each of you did.)*
- **Google Gemini** is the model the app calls to draft skill ratings.
