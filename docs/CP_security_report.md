## Repository Security Findings Report

Generated: 2026-04-15 with GPT-5 mini

Summary: Prioritized findings across backend (Python), frontend (React), config (Docker, compose, CI), Keycloak export, and test artifacts. No fixes applied; this is a non-destructive triage report with file/line references and verification steps.

FINDINGS:

1) Hardcoded Keycloak client secret in realm export
- File: [keycloak-config/realm-export.json](keycloak-config/realm-export.json#L901-L901)
- Lines: 901
- Title: Hardcoded Keycloak client secret
- Explanation: The Keycloak realm export contains plaintext `secret` ("test-secret-key") for a client. Exporting active secrets in repo enables credential theft and impersonation.
- Severity: High
- Confidence: High
- Verification: Open the file and confirm `secret` value at the given line; rotate any referenced secrets in Keycloak.

2) Plaintext secrets in repository `.env`
- File: [.env](.env#L1-L11)
- Lines: 1-11 (notably lines 2, 9, 11)
- Title: Committed environment secrets (DB and Keycloak)
- Explanation: `.env` includes `POSTGRES_PASSWORD=SaV8+5eky`, `KEYCLOAK_CLIENT_SECRET=...`, and `KEYCLOAK_ADMIN_CLIENT_SECRET=...`. Committed env files expose credentials and should not be in VCS.
- Severity: High
- Confidence: High
- Verification: Inspect [.env](.env#L1-L11); ensure `.env` is listed in `.gitignore`, rotate secrets and remove them from history.

3) Insecure defaults and exposed ports in `docker-compose.yml`
- File: [docker-compose.yml](docker-compose.yml#L6-L84)
- Notable lines: POSTGRES_PASSWORD default root ([docker-compose.yml](docker-compose.yml#L6-L7)), PGADMIN_DEFAULT_PASSWORD admin ([docker-compose.yml](docker-compose.yml#L21-L22)), KEYCLOAK_CLIENT_SECRET default ([docker-compose.yml](docker-compose.yml#L82-L84)); multiple `ports:` entries map services to host.
- Title: Default credentials and exposed services in compose
- Explanation: Defaults (`root`, `admin`, `test-secret-key`) and host port mappings can be accidentally used in non-dev environments; services like pgAdmin and Keycloak are mapped to host ports.
- Severity: High
- Confidence: High
- Verification: Inspect [docker-compose.yml](docker-compose.yml#L6-L84) and confirm port mappings and defaults.

4) Hardcoded secrets in CI workflow
- File: [.github/workflows/ci.yaml](.github/workflows/ci.yaml#L63-L71)
- Lines: 63-71 (POSTGRES_USER/POSTGRES_PASSWORD and KEYCLOAK_* secrets)
- Title: CI environment sets plaintext credentials
- Explanation: CI defines `POSTGRES_PASSWORD: root` and `KEYCLOAK_CLIENT_SECRET: test-secret-key`. Hardcoding credentials in workflows is unsafe and exposes secrets to logs and forks.
- Severity: High
- Confidence: High
- Verification: Open [.github/workflows/ci.yaml](.github/workflows/ci.yaml#L63-L71) and replace with secrets from GitHub Actions Secrets.

5) Frontend stores tokens in `localStorage`
- Files: [ui/src/api.js](ui/src/api.js#L1-L20), [ui/src/Login.jsx](ui/src/Login.jsx#L30-L31), [ui/src/App2.jsx](ui/src/App2.jsx#L195-L207), plus others (create/*, index.jsx)
- Notable lines: [ui/src/Login.jsx](ui/src/Login.jsx#L30-L31) saves `access_token`, [ui/src/api.js](ui/src/api.js#L4) reads it
- Title: JWTs and refresh tokens stored in `localStorage`
- Explanation: `localStorage` is accessible to JS and vulnerable to XSS; tokens stored there can be exfiltrated. Prefer httpOnly secure cookies and short-lived tokens.
- Severity: Medium-High
- Confidence: High
- Verification: Search for `localStorage.setItem`/`getItem` across `ui/src` (occurrences found in Login.jsx, App2.jsx, index.jsx, create/*).

6) Flask dev server run with 0.0.0.0 + debug controlled by env
- File: [backend/api.py](backend/api.py#L455-L456)
- Lines: 455-456
- Title: Development server bound to all interfaces and debug toggle
- Explanation: `app.run(host="0.0.0.0", debug=debug_mode)` will expose Werkzeug debugger if `FLASK_DEBUG` becomes true in an environment. Production should use a WSGI server and never enable debug.
- Severity: High
- Confidence: High
- Verification: Inspect [backend/api.py](backend/api.py#L455-L456); check envs for `FLASK_DEBUG` in docker-compose / CI / .env.

7) Default DB credentials used in backend code
- File: [backend/api.py](backend/api.py#L29-L36)
- Lines: 29-36 (POSTGRES_USER/POSTGRES_PASSWORD defaults and DB URI composition)
- Title: Default DB credentials and DB URI built from env vars
- Explanation: Code uses `os.getenv("POSTGRES_PASSWORD", "root")` and constructs a DB URI with credentials — defaults and committed `.env` increase risk; avoid embedding credentials and validate env provisioning.
- Severity: High
- Confidence: High
- Verification: Inspect [backend/api.py](backend/api.py#L29-L36) and ensure migrations / production use secret injection.

8) Keycloak admin token handling and use of full token dict
- File: [backend/auth.py](backend/auth.py#L29-L38)
- Lines: 29-38
- Title: Full token dict retrieved and supplied to `KeycloakAdmin`
- Explanation: `admin_token_dict = keycloak_openid_admin.token(grant_type="client_credentials")` and passing large token objects to admin library increases chances of accidental logging/leakage; store minimal token string and limit logging.
- Severity: Medium
- Confidence: Medium
- Verification: Inspect [backend/auth.py](backend/auth.py#L29-L38); confirm no logging of token contents.

9) Test and load-test artifacts with plaintext passwords/tokens
- Files: [gatling/resources/bodies/login.json](gatling/resources/bodies/login.json#L1-L10), [gatling/simulations/APISimulation.scala](gatling/simulations/APISimulation.scala#L1-L80), [test_backend/**] and other fixtures
- Lines: login.json line 3 (`"password": "test"`) and APISimulation.scala contains `"password" -> "testpass123"` and uses saved `authToken`.
- Title: Test artifacts contain real-looking credentials
- Explanation: Tests and load-test fixtures include plaintext passwords; if committed, these may be used by attackers or leak internal assumptions.
- Severity: Medium
- Confidence: High
- Verification: Inspect the files above; consider moving test credentials to CI secrets or masked fixtures.

10) Use of permissive CORS origin from env with potential wildcard fallback
- File: [backend/api.py](backend/api.py#L1-L30) and requirement for `flask-cors` in [backend/requirements.txt](backend/requirements.txt#L16)
- Lines: CORS init at [backend/api.py](backend/api.py#L24) uses `CORS(app, resources={r"/*": {"origins": frontend_origin}})` where `frontend_origin` may default to `http://localhost:3000` per docs, but docs mention previous permissive wildcard.
- Title: Potentially permissive CORS configuration
- Explanation: CORS is enabled via `flask-cors`. If `frontend_origin` is unset or misconfigured to `*`, APIs may accept cross-origin requests from any origin. Verify `frontend_origin` source and ensure restricted origins and `supports_credentials` only when necessary.
- Severity: Medium
- Confidence: Medium
- Verification: Inspect `frontend_origin` resolution in [backend/api.py](backend/api.py#L1-L30) and any `.env` or deployment env variables controlling it.

11) Frontend uses `http://localhost:8000` and other hardcoded endpoints
- Files: [ui/src/create/create_task.jsx](ui/src/create/create_task.jsx#L59), [ui/src/components/ManageGroupModal.jsx](ui/src/components/ManageGroupModal.jsx#L56)
- Lines: create_task uses `http://localhost:8000/api/groups/user/admin/${userId}`
- Title: Hardcoded backend endpoints (insecure for production)
- Explanation: Hardcoded `http://localhost:8000` may lead to insecure HTTP use in environments that should use HTTPS; also cross-origin calls depend on dev assumptions.
- Severity: Low-Medium
- Confidence: High
- Verification: Search for `http://localhost` and ensure config driven endpoints.

12) No obvious raw SQL string concatenation found (preliminary)
- Files inspected: `backend/services.py`, `backend/models.py`, `backend/api.py` show SQLAlchemy ORM usage (e.g., `db.session.query(...)`). Grep for `execute(` and string formatting found few matches but no clear concatenated SQL in main code paths.
- Title: SQL injection — preliminary low evidence
- Explanation: Most DB access uses SQLAlchemy models/ORM; however, manual SQL or raw `execute` calls should be reviewed manually.
- Severity: Medium (if raw SQL is present)
- Confidence: Medium
- Verification: Manually review any `execute(` calls and search for `f"...{var}..."` or `%` formatting in SQL contexts.

FILES FOR MANUAL REVIEW (high priority)
- [keycloak-config/realm-export.json](keycloak-config/realm-export.json#L1-L2000)
- [.env](.env#L1-L200)
- [docker-compose.yml](docker-compose.yml#L1-L200)
- [.github/workflows/ci.yaml](.github/workflows/ci.yaml#L1-L200)
- [backend/api.py](backend/api.py#L1-L600)
- [backend/auth.py](backend/auth.py#L1-L200)
- [backend/services.py](backend/services.py#L1-L400)
- [ui/src/Login.jsx](ui/src/Login.jsx#L1-L200), [ui/src/api.js](ui/src/api.js#L1-L200), [ui/src/App2.jsx](ui/src/App2.jsx#L1-L300)
- [gatling/resources/bodies/login.json](gatling/resources/bodies/login.json#L1-L40) and [gatling/simulations/APISimulation.scala](gatling/simulations/APISimulation.scala#L1-L120)

RECOMMENDED AUTOMATED SCANS (next steps)
- Secrets detection: `gitleaks detect --source . --report-path gitleaks-report.json`
- Python static analysis: `bandit -r backend/ -f json -o bandit-report.json`
- Python dependency audit: `pip-audit -r backend/requirements.txt -o pip-audit.json`
- Node dependency audit: `cd ui && npm audit --json > npm-audit.json`
- Container scanning: `trivy fs --severity HIGH,CRITICAL .` or `trivy image` on built images
- IaC scanning: `checkov -d . -o json`

NOTES & ASSUMPTIONS
- This review is read-only and non-exhaustive; automated scanners will likely surface additional issues.
- Findings marked "High" should be remediated rapidly: rotate secrets, remove them from git history, and move to secret stores.
- For token storage: prefer httpOnly secure cookies with proper SameSite and CSP and short token lifetimes.

If you want, I can:
- (A) Run the automated scanners and append their results to this report (non-destructive), or
- (B) Prepare a remediation checklist and example changes (CI secrets usage, pre-commit hooks, sanitized export examples) without touching history.


---
Report saved to /memories/session/report.md
