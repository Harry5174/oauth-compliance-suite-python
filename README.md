# Authlete Python Reference Server

A production-grade, **DB-less OAuth 2.0 and OpenID Connect 1.0 Authorization Server** built with [Python](https://www.python.org/) / [FastAPI](https://fastapi.tiangolo.com/) and the [Authlete API](https://www.authlete.com/) as the backend control plane.

This server provides zero-persistence token and authorization lifecycle management. All cryptographic operations, token issuance, client management, and protocol state are delegated entirely to the Authlete SaaS API — meaning this Python application carries no database and no token-side secrets. It is a **pure protocol façade** over Authlete.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Methodology](#architecture--methodology-baseline-testing)
3. [Implemented Endpoints & Capabilities](#implemented-endpoints--capabilities)
4. [Project Structure](#project-structure)
5. [Setup & Execution](#setup--execution)

---

## Overview

This project implements the canonical OAuth 2.0 and OpenID Connect server architecture as specified by the [Authlete](https://www.authlete.com/) reference model. The server is intentionally **stateless**: every API handler receives a request, forwards it to the Authlete backend, and translates the resulting `action` enum into a correct HTTP response — including status codes, headers, and body.

**Core dependencies:**

| Component | Technology |
|---|---|
| Web Framework | FastAPI (ASGI) |
| ASGI Server | Uvicorn |
| Authlete SDK | `authlete-python` |
| HTTP Client (tests) | HTTPX |
| Test Framework | Pytest |
| Runtime | Python ≥ 3.13 |
| Package Manager | [`uv`](https://github.com/astral-sh/uv) |

The workspace is organized as two `uv` sub-packages: `python_oauth_server` (the server) and `compliance_suite` (the test harness).

---

## Architecture & Methodology: Baseline Testing

This project follows a strict **Test-First, Reference-Verified** development methodology. No endpoint is written speculatively. The workflow for every capability is as follows:

### Phase 1 — Establish the Baseline Against the Java Reference

Before implementing any Python endpoint, the compliance suite is run against the **official `java-oauth-server` reference implementation** (Authlete's canonical Java server, running on `http://localhost:8080`). This confirms that the test suite itself is correct and that the expected protocol behaviour is well-defined.

```
TARGET=JAVA pytest compliance_suite/tests/
```

All tests must pass against the Java reference. The passing test output is recorded and treated as the **ground truth specification**.

### Phase 2 — Implement in Python and Verify Equivalence

The Python endpoint is then implemented in `python_oauth_server/api/`, targeting the same Authlete service. The compliance suite is then re-run against the Python server:

```
TARGET=PYTHON pytest compliance_suite/tests/
```

**The Python server is only considered correct when it achieves an identical green-test result to the Java reference.** There is no manual UAT step; compliance is defined purely by the automated suite.

---

## Implemented Endpoints & Capabilities

The following table documents every endpoint currently implemented and the RFC or specification it conforms to.

| Category | Endpoint | HTTP Methods | RFC / Specification | Status |
|---|---|---|---|---|
| **Core Authorization** | `/api/authorization` | `GET`, `POST` | RFC 6749 §3.1 | ✅ Implemented |
| **Core Authorization** | `/api/authorization/decision` | `POST` | RFC 6749 §4.1 (User Decision Handler) | ✅ Implemented |
| **Token Exchange** | `/api/token` | `POST` | RFC 6749 §3.2 | ✅ Implemented |
| **Metadata** | `/.well-known/openid-configuration` | `GET` | OpenID Connect Discovery 1.0 | ✅ Implemented |
| **Metadata** | `/api/jwks` | `GET` | RFC 7517 (JSON Web Key Set) | ✅ Implemented |
| **Token Operations** | `/api/introspection` | `POST` | RFC 7662 (Token Introspection) | ✅ Implemented |
| **Token Operations** | `/api/userinfo` | `GET`, `POST` | OpenID Connect Core §5.3 | ✅ Implemented |
| **Token Operations** | `/api/revocation` | `POST` | RFC 7009 (Token Revocation) | ✅ Implemented |
| **Advanced Security** | `/api/par` | `POST` | RFC 9126 (Pushed Authorization Requests) | ✅ Implemented |
| **AI Agent Provisioning** | `/api/register` | `POST` | RFC 7591 (Dynamic Client Registration) | ✅ Implemented |
| **Grant Lifecycle** | `/api/gm/{grantId}` | `GET`, `DELETE` | RFC 9356 (Grant Management for OAuth 2.0) | ✅ Implemented |
| **Federation** | `/.well-known/openid-federation` | `GET` | OpenID Federation 1.0 | ⏳ In Development |
| **Federation** | `/api/federation/register` | `POST` | OpenID Federation 1.0 (Explicit Registration) | ⏳ In Development |
| **Verifiable Credentials** | `/.well-known/openid-credential-issuer` | `GET` | OID4VCI (Credential Issuer Metadata) | ⏳ In Development |
| **Verifiable Credentials** | `/.well-known/jwt-issuer` | `GET` | RFC 8414 / SD-JWT VC (JWT Issuer Metadata) | ⏳ In Development |

### Endpoint Notes

- **`/api/authorization`** — Implements the complete Authlete `action` dispatcher: `INTERACTION` (renders a Jinja2 login form), `LOCATION` (302 redirect), `NO_INTERACTION` (prompt=none), and `BAD_REQUEST`. Supports both `GET` query string and `POST` form-encoded parameters per RFC 6749.
- **`/api/token`** — Handles `Basic` authentication credential extraction from the `Authorization` header. Dispatches `OK`, `BAD_REQUEST`, `INVALID_CLIENT`, and `INTERNAL_SERVER_ERROR` actions. The deprecated Resource Owner Password Credentials grant (`PASSWORD` action) is intentionally rejected with `unsupported_grant_type`.
- **`/api/introspection`** — Resource Server–authenticated endpoint. Uses a local `ResourceServerDao` for credential validation before forwarding the token to Authlete's standard introspection API, maintaining strict architectural separation.
- **`/api/par`** — Supports both `Basic` Authorization header and form-body credential extraction. Returns `201 Created` on success with a `request_uri` for subsequent use at `/api/authorization`.
- **`/api/register`** — Accepts a raw JSON body per RFC 7591. Does not require an Initial Access Token to align with the `java-oauth-server` reference configuration.
- **`/api/gm/{grantId}`** — `GET` maps to the `QUERY` action; `DELETE` maps to the `REVOKE` action. Requires a valid Bearer token in the `Authorization` header.

---

## Project Structure

```
authlete-python-project/
├── python_oauth_server/           # The FastAPI application (uv workspace member)
│   ├── main.py                    # Application entry point; router registration
│   ├── authlete.properties        # Authlete service credentials (gitignored)
│   ├── api/
│   │   ├── authorization.py       # GET/POST /api/authorization
│   │   ├── authorization_decision.py  # POST /api/authorization/decision
│   │   ├── token.py               # POST /api/token
│   │   ├── metadata.py            # GET /.well-known/openid-configuration, /api/jwks
│   │   ├── userinfo.py            # GET/POST /api/userinfo
│   │   ├── introspection.py       # POST /api/introspection
│   │   ├── revocation.py          # POST /api/revocation
│   │   ├── par.py                 # POST /api/par (RFC 9126)
│   │   ├── register.py            # POST /api/register (RFC 7591)
│   │   └── gm.py                  # GET/DELETE /api/gm/{grantId} (RFC 9356)
│   ├── db/
│   │   └── resource_server_dao.py # In-memory Resource Server credential store
│   └── templates/
│       └── authorization.html     # Jinja2 login/consent form
│
└── compliance_suite/              # Protocol compliance test harness (uv workspace member)
    └── tests/
        ├── conftest.py            # TARGET env var routing (JAVA | PYTHON)
        ├── test_authorization_basics.py
        ├── test_authorization_decision.py
        ├── test_authorization_errors.py
        ├── test_authorization_interaction.py
        ├── test_token_exchange.py
        ├── test_metadata.py
        ├── test_introspection.py
        ├── test_userinfo.py
        ├── test_revocation.py
        ├── test_par.py
        ├── test_register.py
        └── test_grant_management.py
```

---

## Setup & Execution

### Prerequisites

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed
- A valid Authlete account with a configured service. Credentials are stored in `python_oauth_server/authlete.properties`.

### 1. Install Dependencies

From the project root, `uv` resolves and installs all workspace member dependencies using the lockfile:

```bash
uv sync
```

### 2. Run the FastAPI Server

```bash
cd python_oauth_server
uv run uvicorn main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`. The interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs`.

### 3. Execute the Compliance Suite

All test commands must be run from the project root.

**Run against the Java reference server (Phase 1 — Baseline):**

```bash
TARGET=JAVA uv run pytest compliance_suite/tests/ -v
```

> Requires the `java-oauth-server` to be running on `http://localhost:8080`.

**Run against the Python server (Phase 2 — Verification):**

```bash
TARGET=PYTHON uv run pytest compliance_suite/tests/ -v
```

> Requires the Python FastAPI server to be running on `http://localhost:8000`.

**Run a specific test module:**

```bash
TARGET=PYTHON uv run pytest compliance_suite/tests/test_grant_management.py -v
```

**Run with output capture disabled (useful for debugging):**

```bash
TARGET=PYTHON uv run pytest compliance_suite/tests/ -v -s
```

---

## License

See [LICENSE](./LICENSE).
