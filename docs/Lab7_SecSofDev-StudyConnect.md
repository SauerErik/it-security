<p align="center">
    <h>Tim Farnung, Dieter Grünke, Erik Sauer, Leonhard Schneider</h>
</p>
<p>Projekt: StudyConnect</p>

# Lab 7
## SAST Scan
#### Setup
Run once to install Semgrep
```sh
pip install semgrep
```
```sh
semgrep --config=p/security-audit \--config=p/owasp-top-ten \--config=p/cwe-top-25 \--json --output=sast-results.json \.
```