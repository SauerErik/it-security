<p align="center">
    <h>Tim Farnung, Dieter Grünke, Erik Sauer, Leonhard Schneider</h>
</p>
<p>Projekt: StudyConnect</p>

# Lab 7
## SAST Scan
### Setup
Run once to install Semgrep
```sh
pip install semgrep
```

### Scan repository
```sh
semgrep --config=p/security-audit \--config=p/owasp-top-ten \--config=p/cwe-top-25 \--json --output=sast-results.json \.
```

### Categorization of findings
#### CWE Classification

Based on the Semgrep scan results, the identified findings can be categorized into the following CWE categories:

| Category | CWE | Description |
|-----------|------|-------------|
| Authentication Failures / Privilege Management | CWE-250 | Missing non-privileged user definition in Dockerfiles |
| Exposure | CWE-668 | Binding the Flask application to all network interfaces (`0.0.0.0`) |
| Exposure | CWE-489 | Hardcoded debug/test configuration (`TESTING = True`) in test files |

#### SAST Findings Table & Triage

| File | Line | Rule / Vulnerability | CWE Category | Severity | Triage Decision | Justification |
|------|------|----------------------|--------------|----------|-----------------|---------------|
| `backend/Dockerfile` | 19 | Missing User | Authentication Failures / Privilege Management (CWE-250) | ERROR | True Positive | The container runs as the root user by default. This represents a genuine security risk, and a non-privileged user should be defined. |
| `ui/Dockerfile` | 33 | Missing User | Authentication Failures / Privilege Management (CWE-250) | ERROR | True Positive | This container also runs as root. Nginx can and should be configured to run under a non-privileged user (e.g., `nginx`). |
| `backend/api.py` | 456 | Bind to `0.0.0.0` | Exposure (CWE-668) | WARNING | Acceptable Risk | In a Docker environment, binding to `0.0.0.0` is necessary to make the container accessible. Since Gunicorn is correctly used in production, this is considered an acceptable risk within the Flask script. |
| `backend/features/environment.py` | 27 | Hardcoded `TESTING=True` | Exposure (CWE-489) | WARNING | False Positive | This is a dedicated test file (Behave environment configuration). Enabling testing mode here is necessary and legitimate. |
| `test_backend/test_api.py` | 56 | Hardcoded `TESTING=True` | Exposure (CWE-489) | WARNING | False Positive | This is also test code (Pytest fixtures). While the warning is valid for production code, it does not apply to test files. |

### Cross Check: SAST vs. Threat Modeling (Lab 5) Assessment

By comparing the top 8 critical risks identified during our Threat Modeling in Lab 5 with the findings from the Semgrep SAST scan, we can evaluate the effectiveness and limitations of Static Application Security Testing:

***Threats Detected by SAST***
- **R-08: Debug mode or verbose error exposure:** 
  - *SAST Finding:* CWE-489 (Hardcoded `TESTING=True` in test files).
  - *Evaluation:* Semgrep successfully looked for this exact vulnerability category. Even though it was a false positive in this specific context (since the code resides in test files), it proves the scanner actively protects against debug configurations leaking into production.

***Threats not Detected by SAST (and why)***

Static analysis tools inherently struggle with complex business logic. The following risks were not detected:
- **R-02 (IDOR), R-03 (Mass Assignment), R-04 (Group-member disclosure), R-05 (Covert group join):**
  - *Reason:* These are Business Logic Flaws. SAST tools only analyze code syntax and data flow. They cannot "understand" that a `user_id` from a request must match the `user_id` of the database record. Detecting these requires specific custom rules, manual review, or functional security testing (DAST).
- **R-07: Hardcoded or exposed secrets:**
  - *Reason:* Our secrets are primarily stored in `.env` files or `docker-compose.yml`. Semgrep's Python ruleset focuses on source code. This confirms the need for a dedicated Secret Scanning tool (like GitLeaks or TruffleHog), as proposed in Lab 2.
- **R-06: Registration flooding / brute-force requests:**
  - *Reason:* Rate limiting is typically implemented at the infrastructure level (e.g., API Gateway, Nginx) or via specific framework configurations, which standard SAST rules rarely verify effectively.
- **R-01: Token theft from browser storage / XSS session hijack:**
  - *Reason:* While SAST is generally good at finding XSS, Semgrep skipped several advanced JavaScript rules for the React frontend because the Open-Source (OSS) engine lacks certain taint-tracking features required by those specific OWASP rules. Additionally, storing tokens in `localStorage` is often considered a contextual architectural flaw rather than a strict syntax error.

***Unanticipated Findings (beyond Lab 5)***

- **CWE-250 (Execution with Unnecessary Privileges in Docker):**
  - The SAST scan identified a critical security risk (containers running as `root`) that was not part of the Lab 5 Threat Model. The Threat Model focused heavily on application data flows (APIs, JWTs, DB) but overlooked infrastructure and container privileges.

**Conclusion:** 
This comparison highlights the necessity of a Defense in Depth strategy. SAST successfully finds configuration issues and infrastructure flaws (like Docker user privileges), but it completely misses business logic vulnerabilities (like IDOR). To achieve comprehensive security and CRA compliance, SAST must be combined with DAST, Secret Scanning, and Manual Code Reviews.
