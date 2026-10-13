# AVAS — AI Venture Assessment System (beginner-friendly full-stack starter)

**Stack:** React + TypeScript + Vite, FastAPI, SQLAlchemy, PostgreSQL-compatible database, scikit-learn, optional XGBoost/SHAP, ReportLab.

## What is included
- Responsive venture-assessment dashboard
- Register/login using signed JWT access tokens
- FastAPI endpoints for health, auth, assessment, history, and PDF report
- Database models for users and saved assessments
- A transparent 0–100 readiness rubric
- Separate rule-based growth-potential indicator, explicit positive signals and priority gaps
- Financial snapshot highlighting runway and whether entered monthly revenue covers burn
- A Random Forest demo classifier trained on 10,000 generated synthetic records
- Training/evaluation pipeline for a properly labeled CSV of real startup outcomes
- Optional XGBoost model comparison and optional SHAP explanation
- PDF assessment report
- PostgreSQL configuration with SQLite as an easy local fallback

## Critical limitation: synthetic vs real data
The included 10,000-row dataset is **synthetic**. Its target label is generated from a rule for testing the pipeline. High scores or metrics on it do not prove the model can predict real startup success. Do not use its probability for investment decisions or describe it as validated. For real-world use, collect legally usable, representative startup records with documented outcomes and label definitions.

## Requirements
- Python 3.12 recommended
- Node.js 20+
- PostgreSQL 15+ (optional for first run; SQLite is default for easy local setup)
- VS Code recommended

## Folder structure
```text
avas_complete/
  backend/
    app/
      main.py, config.py, database.py, models.py, schemas.py
      security.py, assessment.py, reporting.py
    ml/
      generate_demo_data.py, train_model.py, compare_models.py
      data/real_dataset_template.csv
    requirements.txt
    requirements-ml.txt
    .env.example
  frontend/
    src/App.tsx, src/main.tsx, src/styles.css
    package.json, vite.config.ts, tsconfig.json, index.html
```

# Windows setup (beginner)

## A. Download and extract
Extract this ZIP, then open the `avas_complete` folder in VS Code.

## B. Start backend
Open terminal 1:
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m ml.generate_demo_data
.\.venv\Scripts\python.exe -m ml.train_model
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
If you already activated the environment, you may use `python` and `pip` instead. Using `.venv\Scripts\python.exe` avoids PowerShell activation-policy issues.

Open:
- API health: http://127.0.0.1:8000/api/health
- Interactive API docs: http://127.0.0.1:8000/docs

## C. Start frontend
Open terminal 2:
```powershell
cd frontend
npm install
npm run dev
```
Open the localhost URL Vite prints (usually http://localhost:5173).

## D. First use
1. Register an account in the UI.
2. Sign in.
3. Fill the assessment form and press **Assess venture**.
4. Your assessment is saved to the configured database.
5. Use history to view saved assessments and download a PDF report.

# PostgreSQL setup (optional, recommended when ready)
1. Install PostgreSQL and create a database/user, for example:
```sql
CREATE USER avas_user WITH PASSWORD 'change_this_password';
CREATE DATABASE avas_db OWNER avas_user;
```
2. Edit `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg://avas_user:change_this_password@localhost:5432/avas_db
JWT_SECRET=replace-with-a-long-random-secret
```
3. Restart backend. Tables are created automatically for this learning MVP. For production, use Alembic migrations rather than `create_all()`.

# Optional model packages
From `backend/`:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
.\.venv\Scripts\python.exe -m ml.compare_models
```
XGBoost and SHAP are optional. If installation fails on your computer, the core app works without them.

# Real data training
1. Start with `ml/data/real_dataset_template.csv`.
2. Replace it with a legally obtained and documented dataset; do not merely change synthetic labels and call them real.
3. Define the target label precisely (for example, survival after 36 months, a specified revenue milestone by a fixed date, or a funding event within a fixed period).
4. Make sure each row has the required feature columns and a 0/1 `positive_outcome` label.
5. Run:
```powershell
.\.venv\Scripts\python.exe -m ml.train_model --input ml/data/your_labeled_dataset.csv
```
The training script uses a held-out stratified test split. For serious evaluation, add time-based/company-group splits, leakage checks, calibration, subgroup analysis, and external validation. Do not train on information that became known after the outcome date.

# Dataset feature definitions
Ratings are 1–5. `financial_runway_months` is months of cash remaining. Monetary values must use one consistent currency and period. `target_market_size_millions` is in millions of that currency. `has_prototype` and `has_competitor_research` are 0/1. `positive_outcome` must be an observed, consistently defined label, not a subjective guess.

# Security and production checklist
- Set a strong random `JWT_SECRET`; never commit `.env`.
- Add email verification, password reset, rate limiting, HTTPS, backups, monitoring and Alembic migrations.
- Add authorization checks before exposing records.
- Audit model bias and avoid protected characteristics and unjustified proxies.
- Add source provenance, consent/licensing checks, and retention policies for uploaded founder data.
- Outputs are decision support only, not investment advice.

## Phase 2 update: explainability and financial insights
The assessment result now includes:
- `growth_potential_score`: a separate 0–100 heuristic indicator, not a trained prediction.
- `explainability.positive_signals` and `explainability.priority_gaps`: short descriptions derived from entered 1–5 ratings.
- `explainability.financial_snapshot`: entered runway, net monthly burn (monthly burn minus monthly revenue), revenue-vs-burn check, and runway alert.
- PDF reports include the growth indicator, explanation, and financial snapshot.
- Previously saved assessments remain viewable; older records display a clear legacy-result message for fields that were not calculated at the time.

The explanation panel is deliberately labeled as rule-based. It is not SHAP and should not be described as causal model explainability.

## Verify the backend update
From the `backend` directory with the project virtual environment installed:
```powershell
.\\.venv\\Scripts\\python.exe -m unittest discover -s tests
```

## Upgrade an existing local copy
1. Stop the backend and frontend terminals with `Ctrl+C`.
2. Extract the updated ZIP into a new folder.
3. If you want to keep local accounts/history, copy your existing `backend/avas.db` and `backend/.env` into the updated project's `backend` folder (if those files exist). Do not share `.env` publicly.
4. Start the backend and frontend using the setup steps above. If dependencies are already installed in the new folder, run `npm install` in `frontend` before `npm run dev`.


## Phase 3: local SHAP model explanations
- When a trained tree-model artifact is present and SHAP is installed, AVAS attempts to calculate per-assessment TreeSHAP contributions for the model's positive class.
- The result page and PDF show the strongest positive and negative contributions, the entered feature values, and a note about interpretation.
- SHAP is optional: if the package is not installed, no compatible model is loaded, or the explainer fails, the rest of the assessment continues and the UI clearly marks SHAP as unavailable.
- These are model contributions, not causal effects. A model trained on the included synthetic dataset remains unvalidated and its contribution analysis is only a technical demonstration.

### Enable SHAP on Windows
From the `backend` folder, run:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
```
Then restart the backend and create a new assessment. If SHAP installation fails, the app continues to work without it.


## Phase 4 — Pitch deck review

The authenticated `POST /api/pitch-deck/analyze` endpoint accepts a text-based PDF (maximum 10 MB and 50 pages), extracts selectable text in memory, and runs a heuristic checklist for problem, solution, market opportunity, business model, traction, competition, go-to-market, team, financials, and funding ask. It returns evidence snippets, topics not detected, and suggested founder questions. The uploaded PDF is not saved by this endpoint.

Install updated backend requirements after updating files: `python -m pip install -r requirements.txt`. The frontend adds a **Pitch deck review** workspace page. Scanned/image-only PDFs need OCR, which is not included. This is keyword-based document triage, not a generative-AI review or investment recommendation.

### Phase 5: optional AI-assisted pitch-deck review

The Pitch Deck Review page now offers a separate **AI review** button. It sends up to 28,000 characters of extracted PDF text to an OpenAI-compatible Chat Completions API and presents an executive summary, potential strengths, concerns, financial observations, claims to verify, founder questions, and a due-diligence checklist. The standard keyword checklist continues to work without an API key.

To enable the AI review, edit `backend/.env` (do not place the key in frontend code):

```env
LLM_API_KEY=your_private_provider_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

Use the model name and base URL supported by your chosen provider. Restart the backend after editing `.env`. Check `/api/health` for `ai_review_configured: true`. The feature requires network access and may incur provider charges. Never commit `.env`, share your API key, or upload confidential pitch decks unless the provider's privacy and retention terms are acceptable to you. Only extracted text (not the original PDF file) is sent; the endpoint does not persist the PDF. The text is truncated at 28,000 characters.

The AI output is generated and may be wrong. Evidence quotations should be checked against the deck; external claims are not independently verified. It does not produce an investment recommendation, a success probability, or a validated startup score. The API key stays on the backend.


### Phase 6: structured startup data extraction

The Pitch Deck Review workspace adds **Extract data**. It asks the configured OpenAI-compatible model to extract startup name, industry, problem, solution, target customer, revenue model, funding ask, monthly revenue and burn, runway, team size, paying customers, market size, and traction. Each candidate value must include an exact evidence quotation that is checked against the extracted PDF text; values without a matching quote are shown as not found. Users can edit the values and export the review as CSV.

The feature uses the same optional `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` settings as Phase 5. It sends up to 28,000 characters of extracted text to that provider; the PDF itself is processed in memory and is not saved by the endpoint. This is draft extraction, not independent verification. Review every field and evidence quote before using the CSV. Scanned/image-only PDFs still require OCR, which is not included.

### Phase 7: assessment integration and discrepancy report

Phase 7 connects reviewed Phase 6 pitch-deck extraction to the assessment workflow:

- **Use in assessment form** copies supported extracted fields into the venture profile (startup name, industry, monthly revenue, monthly burn, runway, funding ask, market size, and paying-customer count). It does not automatically submit an assessment.
- **Compare against assessment form** compares extracted values with the currently entered profile and labels each as consistent, different, or needing review/missing.
- **Export discrepancy report** downloads the comparison as CSV. Numeric values allow a 5% tolerance for ordinary numeric fields; market size is normalized to currency millions where units can be interpreted. Always confirm units and currency manually.
- Values that cannot be parsed are left out of the import rather than guessed. The comparison is a review aid, not verification of the pitch deck's claims.

No database migration is required for Phase 7. The existing optional LLM configuration remains required for Phase 6 extraction; checklist review still works without it.

## Phase 8 — Venture Analytics Dashboard

Phase 8 adds a **Venture analytics** workspace to review your saved assessment data.

### Included
- Account-scoped analytics endpoint: `GET /api/analytics` (only returns the signed-in user's own saved assessments).
- KPI cards for saved assessments, average readiness, high-risk count, and distinct industry labels.
- Readiness score distribution, risk distribution, monthly trend, and industry comparison charts.
- Recent assessment table and CSV export.
- Empty-state messaging when no assessments have been saved yet.

### How to use
1. Start the backend and frontend as described in the setup section.
2. Sign in and open **Venture analytics** in the left navigation.
3. Run some assessments first if the dashboard is empty.
4. Use **Refresh** after creating new assessments, or **Export CSV** to download the assessment rows.

Analytics are computed from saved records; they do not represent independently verified business performance or predict investment outcomes.

### Phase 8 testing
The backend analytics aggregation has focused tests for totals, risk counts, industry averages, monthly trend, score-band counts, and empty data.

## Phase 9 — Comparative Venture Evaluation

The sidebar now includes **Compare ventures**. Select between two and four saved assessments and compare their readiness scores, risk labels, growth indicators, financial runway, monthly net burn, positive signals, priority gaps, risk flags, and recommendations. Export the selected comparison to CSV for Excel review.

The comparison API is `POST /api/compare` with JSON body `{"assessment_ids":[1,2]}`. It requires a signed-in user and only returns assessments owned by that account. Duplicate IDs, fewer than two IDs, more than four IDs, and IDs outside the user's account are rejected. The comparison is descriptive decision support: it does not verify claims or recommend an investment.

### Phase 9 update
Use the Phase 9 ZIP as a complete project folder. To preserve existing local data, copy your current `backend/.env` and database file into the new `backend` folder before starting it. Install backend requirements and frontend npm dependencies using the setup steps above.

## Phase 10 — Investment Memo & Report Generator

Phase 10 adds an **Investment memo** workspace and two authenticated, account-scoped endpoints:

- `GET /api/assessments/{assessment_id}/investment-memo` returns a structured JSON memo.
- `GET /api/assessments/{assessment_id}/investment-memo.pdf` generates and downloads a formatted PDF memo.

The memo contains an executive summary, assessment snapshot, available financial overview, positive signals, priority gaps, risk flags, SWOT snapshot, recommended next steps, and an evidence-gap / due-diligence checklist. The UI lets a signed-in user choose one saved assessment, preview the memo, and download the PDF. New assessments now preserve the entered input snapshot for future memo generation; older assessments remain supported but may show financial values as not recorded.

### How to use Phase 10
1. Install backend requirements and frontend dependencies using the setup instructions above.
2. Start backend and frontend and sign in.
3. Run and save an assessment if needed.
4. Open **Investment memo** in the left navigation.
5. Select an assessment, click **Generate memo**, and use **Download PDF**.

The memo is generated deterministically from saved AVAS data; it is not an independent external research report or an automated investment recommendation. Financial figures, pitch-deck claims, legal matters, market size and customer traction are not independently verified. Older saved assessments do not have the new full input snapshot, so missing financial fields are labelled as not recorded rather than guessed.

### Phase 10 testing
Backend compilation succeeded and the full backend test suite passed (16 tests). Frontend production build was not verified because npm dependency installation timed out in the build environment.

## Phase 11 — Startup Portfolio Management

Phase 11 adds an account-scoped portfolio workspace for organizing saved startup assessments after they have been evaluated.

### Features
- Add any saved assessment to a personal startup portfolio.
- Track an opportunity through **Watching**, **Due diligence**, **Active**, **On hold**, or **Passed**.
- Keep editable review notes (up to 5,000 characters per startup).
- View readiness and risk snapshots plus a portfolio average and due-diligence count.
- Remove an item from the portfolio without deleting its saved assessment/history.
- Backend ownership checks prevent adding or editing another account's records.

### New API routes
- `GET /api/portfolio` — list the signed-in user's portfolio.
- `POST /api/portfolio` — add a saved assessment (`assessment_id`, optional `status`, optional `notes`).
- `PATCH /api/portfolio/{entry_id}` — update `status` and/or `notes`.
- `DELETE /api/portfolio/{entry_id}` — remove the tracking entry only.

Portfolio entries are stored in a new `portfolio_entries` database table. Existing database tables are not altered by this phase; the app's existing `Base.metadata.create_all()` startup creates the new table automatically.

### How to use
1. Start the backend and frontend as described in the setup section above.
2. Sign in and run at least one assessment.
3. Open **Startup portfolio** from the left sidebar.
4. Select a saved assessment, choose a starting status, add optional notes, and click **Add to portfolio**.
5. Update status or notes on a tracked startup and click **Save changes**. Use **Remove** to stop tracking it without deleting the original assessment.

## Phase 12 — Investment Decision Support

Phase 12 adds a signed-in-account-scoped **Investment review** page with portfolio-level summary metrics, deterministic priority alerts, saved-assessment risk distribution, portfolio status counts, and readiness progress trends for startup names with multiple saved assessments.

New endpoint: `GET /api/decision-support` (requires `Authorization: Bearer <token>`). It returns summary metrics, risk distribution, portfolio status counts, alert prompts, and chronological snapshots grouped by startup name. Alerts can be triggered by high risk, recorded runway under six months, readiness under 50, and saved due-diligence entries with recorded priority gaps. They are screening prompts, not investment advice or failure predictions. Trends assume assessments with the same startup name refer to the same business; verify that assumption and use consistent units/inputs.

No existing database columns are changed. The feature reads existing assessment and portfolio records.

## Phase 13 — Advanced Analytics Dashboard

Phase 13 expands the account-scoped analytics page with:
- readiness-factor breakdown from saved input snapshots (rating dimensions normalized from 1–5 to 0–100; binary checks shown as 0 or 100)
- financial KPI summaries for monthly revenue, burn, funding ask and runway
- runway-band distribution and startup-level financial snapshots
- missing-input handling for older assessments and a note that each startup's currency may differ
- existing score/risk distribution, monthly trend, industry comparison and CSV export remain available

Open **Venture analytics / Advanced analytics** in the sidebar after running the frontend and backend. The charts use saved assessment inputs; factor averages are descriptive input summaries, not SHAP feature importance or investment predictions. Financial values should only be compared when entered in the same currency and on a consistent basis.

### Phase 13 test notes
Run backend tests from the `backend` directory:

```powershell
python -m pytest -q
```

## Phase 14 — Reports & Data Management
- Export an account-scoped assessment summary as CSV.
- Export an Excel workbook with `Assessments` and `Financial snapshots` worksheets.
- Download a portable JSON backup of assessment results and available input snapshots (never account credentials).
- Import a versioned AVAS JSON backup. Imports are validated, limited to 500 records / 10 MB, assigned to the currently signed-in account, and added without overwriting existing records.
- PDF assessment reports and investment memos remain available from their existing pages.

### Phase 14 use
1. Sign in and open **Reports & data** in the sidebar.
2. Choose CSV, Excel, or JSON backup export.
3. To restore, select a JSON backup created by AVAS and confirm the import count.
4. Review imported records; import does not deduplicate similar startup records automatically.

Excel values use the units entered by the user; currencies are not standardized. AVAS is an educational decision-support tool, not investment advice.


## Phase 15 — Final integration, security & deployment

Phase 15 adds configurable frontend API URLs (`frontend/.env`), database-aware health checks, common response security headers, stricter CORS configuration, and production startup checks for JWT secret strength and trusted frontend origin. It also adds a dedicated `DEPLOYMENT.md` with setup, release verification, deployment steps, and remaining production limitations.

Before using this release, follow the **Local release check** in `DEPLOYMENT.md`. In this execution environment the backend test suite could not fully run because the `python-jose` dependency is not installed, and the frontend production build was not verified because Node dependencies are not installed. Install the listed requirements and run the checks on your machine.
