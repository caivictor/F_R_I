# SECURITY VULNERABILITIES LEDGER

## SEC-001: Path Traversal Vulnerability in Static File Serving Handler

- Status: CLOSED
- Severity: HIGH
- Found by: security
- Component: backend/app/main.py

Vulnerability Description:
In `backend/app/main.py`, the fallback route `serve_frontend(full_path: str)` computes `file_path = FRONTEND_DIST / full_path` without resolving and verifying that the canonical target path remains strictly bounded within the `FRONTEND_DIST` directory tree.

Exploit Scenario:
An attacker sending requests with directory traversal sequences (e.g., `GET /../../etc/passwd` or `GET /....//....//etc/shadow`) could cause `file_path` to escape the static build directory and return arbitrary system files.

Security Impact:
Arbitrary local file inclusion / unauthorized read access to system files outside the web root.

Recommended Remediation:
Resolve `file_path` canonically using `.resolve()` and verify `str(resolved_path).startswith(str(FRONTEND_DIST.resolve()))` before verifying existence and returning `FileResponse`.

History:
- security: opened
- orchestrator: set FIX-READY (backend-dev: Added canonical path resolution and boundary containment validation in serve_frontend)
- security: closed (retested path traversal payload /../../etc/passwd in test_sec_001_path_traversal_protection and verified containment to index.html)

