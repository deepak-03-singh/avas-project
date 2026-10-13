# AVAS Phase 15 — Integration, Security & Deployment

This release adds final integration safeguards and deployment configuration. It is still an educational MVP; complete the production checklist before using real investor/founder data.

## Configuration

### Backend (`backend/.env`)
Copy `.env.example` to `.env`. Keep secrets out of source control.

- `DATABASE_URL`: SQLite for local learning, PostgreSQL for shared deployments.
- `JWT_SECRET`: replace the example with a randomly generated secret. In production it must be at least 32 characters and must not be the development default.
- `ENVIRONMENT`: use `development` locally. Set to `production` only behind HTTPS and after setting a strong secret.
- `FRONTEND_ORIGIN`: exact frontend origin, such as `http://localhost:5173` locally or your deployed HTTPS origin.
- `ACCESS_TOKEN_MINUTES`: access-token lifetime.
- `LLM_API_KEY`: optional; keep only in backend environment configuration.

Generate a local secret in PowerShell with:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Frontend (`frontend/.env`)
Copy `.env.example` to `.env` and set `VITE_API_BASE_URL` to the backend origin without `/api`, for example `https://api.example.com`. Vite environment variables are public in the built JavaScript; never put secrets here. Restart `npm run dev` after changing this value.

## Local release check (Windows PowerShell)

Backend terminal:
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend terminal:
```powershell
cd frontend
npm install
npm run build
npm run dev
```

Verify `http://127.0.0.1:8000/api/health` returns `status: ok` and `database: connected`; check `http://127.0.0.1:8000/docs` for the API schema. Then manually verify registration/login, create assessment, history, comparison, analytics, portfolio, pitch-deck review, PDF/Excel/CSV export, and JSON backup/import.

## Phase 15 security and integration changes

- Health endpoint now performs a lightweight database connection check and returns HTTP 503 if the database is unavailable; it never returns credentials or connection strings.
- Response middleware sets common security headers. HSTS is added only when `ENVIRONMENT=production`.
- CORS methods and headers are explicit rather than wildcarded.
- Production startup refuses the known development JWT secret / short secrets and refuses a wildcard frontend origin.
- Frontend API base URL can be configured with `VITE_API_BASE_URL` instead of being hard-coded across pages.
- `.gitignore` covers local environment files, databases, build output, and test coverage artifacts.

## Deployment outline

1. Provision a supported Python runtime and Node.js 20+ build environment.
2. Use PostgreSQL, a managed secret store, backups, and a least-privilege database account.
3. Configure `DATABASE_URL`, `JWT_SECRET`, `ENVIRONMENT=production`, `FRONTEND_ORIGIN`, and optional LLM settings on the server (not in Git).
4. Build the frontend with `npm run build` and serve `frontend/dist` using a static host or Nginx.
5. Run the API with a production ASGI process manager behind a TLS-terminating reverse proxy; do not expose the development `--reload` server to the internet.
6. Apply schema migrations before future schema changes. This MVP currently uses `create_all()` and does not yet include Alembic migrations.
7. Run tests and a manual smoke test after every deployment. Monitor application/database errors and test backup restoration.

## Known limitations before real-world use

- The demo dataset is synthetic; prediction scores are not validated forecasts.
- The readiness explanation is rule-based; optional SHAP support depends on a compatible trained model and installed extras.
- Authentication currently uses bearer tokens; rate limiting, email verification, password reset, audit logging, and account lifecycle workflows remain to be implemented.
- Add Alembic migrations, automated end-to-end/browser tests, dependency vulnerability scanning, structured logs, monitoring, and tested backup/restore before production use.
- Pitch deck extraction supports text-based PDFs only; scanned PDFs require OCR. Do not upload confidential documents unless data handling/provider terms are acceptable.
- This tool is decision support, not investment advice. Human review and independent due diligence remain necessary.
