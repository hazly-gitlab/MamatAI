# Security & Hardening Policy

1. **Role-Based Access Control (RBAC)**: Admin, User, Read-only.
2. **Safe Tool Execution**: Dangerous tools require confirmation prompts.
3. **Database Safeguards**: SQL tools strictly enforce `SELECT` queries and reject destructive keywords (`DROP`, `DELETE`, `UPDATE`).
4. **Header Protection**: Enforced Content-Security-Policy (CSP), CORS, and X-Frame-Options.
