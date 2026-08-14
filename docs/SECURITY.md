# Security hardening protocols

This project treats security as a first-class citizen, implementing state-of-the-art protections across both the software and infrastructural layers.

---

## 1. Secret Management
- Real keys, API passcodes, and database passwords are **never** committed to the codebase.
- Credentials must be parsed into containers strictly using environment variables via `.env`.

## 2. Password Hashing
- Accounts are secured using `bcrypt` password hashing with automatically generated salts.
- Employs directly managed Python-bcrypt layers to prevent version incompatibility with modern environments.

## 3. SQL Injection Protection
- Database queries utilize SQLAlchemy's object-relational mapping (ORM) with fully parameterized parameters.
- Natural language safe-SQL execution tools validate commands against a strict syntax allowlist, completely blocking modify, insert, delete, drop, and truncate statement executions.

## 4. SSRF Prevention
- Dynamic HTTP request execution tools parse target hostnames and validate them against `ALLOWED_HTTP_DOMAINS` prior to network connection.
- Requests to localhost, private networks, or internal loopback subnets are strictly denied.

## 5. Sliding-Window Rate Limiting
- System endpoints are protected using IP-based sliding window limiters.
- Rate-limiting violations return clean HTTP `429 Too Many Requests` responses.
