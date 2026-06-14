# Lab 8

## Part A: Manual CVE Hunt

### List of direct dependencies

The list of direct dependencies was created using the tool `pipreqs`. Since it is present in the requirements.txt, it is usable out of the box. 

To explicitly avoid overwriting the existing requirements list, the command used was: `pipreqs --savepath direct_reqs.txt ./` (from directory `backend/`). Results see [direct_reqs.txt](../backend/direct_reqs.txt)

NOTEs: 
- The version numbers do not match the one's used in the project's [requirements.txt](../backend/requirements.txt).
- The wrong keycloak package was detected and has to be manually corrected.

The corrected output with the respective package version is listed below:
```
behave==1.3.3
Flask==3.1.2
flask-cors==6.0.1
Flask-SQLAlchemy==3.1.1
python-keycloak==5.8.1
python-dotenv==1.1.1
SQLAlchemy==2.0.43
```

### CVE Findings Table

The following table lists some of the critical vulnerabilities found in the project’s dependencies. Each entry includes the CVE ID, CVSS score, affected version range, the version that fixes the issue, and the dependency type. All findings were initially looked up on NVD (nvd.nist.gov) and successfully cross-checked on OSV (osv.dev).

| CVE ID | CVSS | Affected Version Range | Fix Version | Dep. Type |
| --- | --- | --- | --- | --- |
| CVE-2026-28684 | 6.6 | < 1.2.2 | 1.2.2 | Direct |
| CVE-2026-44432 | 7.5 | 2.6.0 - 2.6.x | 2.7.0 | Transitive |
| CVE-2026-31958 | 7.5 | < 6.5.5 | 6.5.5 | Transitive |
| CVE-2026-44896 | 6.1 | ≤ 3.2.0 | 3.2.1 | Transitive |


### Package List Excerpts

Below is an excerpt of the project’s dependencies, annotated to show which packages were analyzed and whether vulnerabilities were found. Packages marked with ⚠️ have known CVEs, while ✅ indicates no issues were detected.

| Package | Version | Status |
| --- | --- | --- |
| flask | 3.1.2 | ✅ |
| python-dotenv | 1.1.1 | ⚠️ CVE-2026-28684 |behave==1.3.3
| flask-cors | 6.0.1 | ✅ | 
| Flask-SQLAlchemy | 3.1.1 | ✅ |
| python-keycloak | 5.8.1 | ✅ |
| SQLAlchemy | 2.0.43 | ✅ |
| behave | 1.3.3 | ✅ |
| urllib3 | 2.6.0 | ⚠️ CVE-2026-44432, CVE-2026-44431 |
| tornado | 6.5.2 | ⚠️ CVE-2026-31958, CVE-2026-35536 |
| mistune | 3.1.4 | ⚠️ CVE-2026-44896, CVE-2026-44899 |


## Part B: SBOM and Automated Scan
#### Generate SBOM
Install cdxgen with npm `npm install -g @cyclonedx/cdxgen' and run 'cdxgen --output sbom.json --json-pretty`,
this generates the sbom file [sbom.json](../backend/sbom.json).

#### Count components
Using `jq '.components | length' sbom.json` or `python3 -c "import json; data=json.load(open('backend/sbom.json')); print(len(data['components']))"
` counts the amount of components in the sbom.json when in the backend folder.

The amount in this projects sbom is: **146 components**