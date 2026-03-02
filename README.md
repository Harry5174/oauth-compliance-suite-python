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
| Containerization | Docker / Docker Compose |

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
| **Federation** | `/.well-known/openid-federation` | `GET` | OpenID Federation 1.0 | ✅ Implemented |
| **Federation** | `/api/federation/register` | `POST` | OpenID Federation 1.0 (Explicit Registration) | ✅ Implemented |
| **Verifiable Credentials** | `/.well-known/openid-credential-issuer` | `GET` | OID4VCI (Credential Issuer Metadata) | ✅ Implemented |
| **Verifiable Credentials** | `/.well-known/jwt-issuer` | `GET` | RFC 8414 / SD-JWT VC (JWT Issuer Metadata) | ✅ Implemented |
| **Verifiable Credentials** | `/api/credential` | `POST` | OID4VCI (Credential Endpoint) | ✅ Implemented |

### Endpoint Notes

- **`/api/authorization`** — Implements the complete Authlete `action` dispatcher: `INTERACTION` (renders a Jinja2 login form), `LOCATION` (302 redirect), `NO_INTERACTION` (prompt=none), and `BAD_REQUEST`. Supports both `GET` query string and `POST` form-encoded parameters per RFC 6749.
- **`/api/token`** — Handles `Basic` authentication credential extraction from the `Authorization` header. Dispatches `OK`, `BAD_REQUEST`, `INVALID_CLIENT`, and `INTERNAL_SERVER_ERROR` actions. The deprecated Resource Owner Password Credentials grant (`PASSWORD` action) is intentionally rejected with `unsupported_grant_type`.
- **`/api/introspection`** — Resource Server–authenticated endpoint. Uses a local `ResourceServerDao` for credential validation before forwarding the token to Authlete's standard introspection API, maintaining strict architectural separation.
- **`/api/par`** — Supports both `Basic` Authorization header and form-body credential extraction. Returns `201 Created` on success with a `request_uri` for subsequent use at `/api/authorization`.
- **`/api/register`** — Accepts a raw JSON body per RFC 7591. Does not require an Initial Access Token to align with the `java-oauth-server` reference configuration.
- **`/api/gm/{grantId}`** — `GET` maps to the `QUERY` action; `DELETE` maps to the `REVOKE` action. Requires a valid Bearer token in the `Authorization` header.
- **`/.well-known/openid-credential-issuer`** — Delegates to `authlete_api.credentialIssuerMetadata()` via a `CredentialIssuerMetadataRequest` DTO. Returns the OID4VCI Credential Issuer Metadata document describing the Verifiable Credentials this IdP can issue. Dispatches `OK` (200), `NOT_FOUND` (404), and `INTERNAL_SERVER_ERROR` (500) actions.
- **`/.well-known/openid-federation`** — Delegates to `authlete_api.federationConfiguration()` via a `FederationConfigurationRequest` DTO. Returns a signed JWT (Entity Statement) representing this IdP's trust metadata. On `OK`, the response is served with the spec-required `application/entity-statement+jwt` content type. Dispatches `OK` (200), `NOT_FOUND` (404), and `INTERNAL_SERVER_ERROR` (500) actions.
- **`/api/federation/register`** — Accepts a raw Entity Statement JWT in the request body. Delegates to `authlete_api.federationRegistration()` via a `FederationRegistrationRequest` DTO. Registers the client if the Trust Chain is valid. Dispatches `CREATED` (201), `BAD_REQUEST` (400), and `INTERNAL_SERVER_ERROR` (500) actions.
- **`/api/credential`** — OID4VCI Credential Endpoint. Validates the Bearer access token, extracts the JSON credential request payload, and delegates to `authlete_api.credentialSingleIssue()` via a `CredentialSingleIssueRequest` DTO with a `CredentialIssuanceOrder`. Dispatches `OK` (200), `BAD_REQUEST` (400), `UNAUTHORIZED` (401), `FORBIDDEN` (403), and `INTERNAL_SERVER_ERROR` (500) actions.
- **`/.well-known/jwt-issuer`** — SD-JWT Issuer Metadata Endpoint. Delegates to `authlete_api.credentialJwtIssuerMetadata()` via a `CredentialJwtIssuerMetadataRequest` DTO. Returns the JWT issuer configuration including signing key references (`jwks_uri`). Dispatches `OK` (200), `NOT_FOUND` (404), and `INTERNAL_SERVER_ERROR` (500) actions.

---

## Project Structure

```
authlete-python-project/
├── Dockerfile                     # Container build (Python 3.13-slim + uv)
├── docker-compose.yml             # Single-command server launch on port 8000
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
│   │   ├── gm.py                  # GET/DELETE /api/gm/{grantId} (RFC 9356)
│   │   ├── federation_configuration.py  # GET /.well-known/openid-federation
│   │   ├── federation_registration.py   # POST /api/federation/register
│   │   ├── credential_issuer_metadata.py # GET /.well-known/openid-credential-issuer
│   │   ├── credential.py          # POST /api/credential (OID4VCI)
│   │   └── jwt_issuer_metadata.py # GET /.well-known/jwt-issuer (RFC 8414)
│   ├── db/
│   │   ├── resource_server_dao.py # In-memory Resource Server credential store
│   │   └── user_dao.py            # In-memory user credential store
│   ├── resources/
│   │   ├── resource_servers.json  # Resource Server seed data
│   │   └── users.json             # User seed data
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
        ├── test_grant_management.py
        ├── test_federation_configuration.py
        ├── test_federation_registration.py
        ├── test_credential_issuer_metadata.py
        ├── test_credential_endpoint.py
        └── test_jwt_issuer_metadata.py
```

---

## Setup & Execution

### Prerequisites

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed (for local development)
- [Docker](https://docs.docker.com/get-docker/) installed (for containerized deployment)
- A valid Authlete account with a configured service. Credentials are stored in `python_oauth_server/authlete.properties`.

### Option A: Docker Compose (Recommended)

The fastest way to start the server — mirrors the `java-oauth-server` Docker workflow:

```bash
docker compose up
```

The server will be available at `http://localhost:8000`. To rebuild after code changes:

```bash
docker compose up --build
```

To run in detached mode:

```bash
docker compose up -d
```

### Option B: Local Development with `uv`

**1. Install Dependencies**

From the project root, `uv` resolves and installs all workspace member dependencies using the lockfile:

```bash
uv sync
```

**2. Run the FastAPI Server**

```bash
cd python_oauth_server
uv run uvicorn main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`. The interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs`.

### Executing the Compliance Suite

All test commands must be run from the project root.

**Run against the Java reference server (Baseline):**

```bash
TARGET=JAVA uv run pytest compliance_suite/tests/ -v
```

> Requires the `java-oauth-server` to be running on `http://localhost:8080`.

**Run against the Python server (Verification):**

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

## Known Issues & Upstream Bugs

### `KeyError: 'NO_CONTENT'` — Missing Enum in `authlete-python` v1.3.0

**Status:** Temporarily patched in this codebase. Awaiting upstream fix.

**Affected component:** `authlete-python` PyPI package (v1.3.0)

**Symptom:** When a `DELETE /api/gm/{grantId}` request results in a successful revocation, the
Authlete V3 backend returns the action string `"NO_CONTENT"` in its JSON response. The SDK
deserialization in `authlete/types/jsonable.py` (line 64) attempts:

```python
return attrType[value]  # GrantManagementAction['NO_CONTENT']
```

The published SDK is missing two enum members in `GrantManagementAction`:

| Missing Member | Expected HTTP Status |
|---|---|
| `NO_CONTENT` | `204 No Content` (successful DELETE) |
| `NOT_FOUND` | `404 Not Found` (grant does not exist) |

This raises `KeyError: 'NO_CONTENT'`, which crashes the ASGI worker and causes the client to see
`"Server disconnected without sending a response"` rather than a valid `204`.

**Temporary patch applied:** [`sdk_compat_patch.py`](./python_oauth_server/sdk_compat_patch.py) is
imported and executed at the very top of `main.py`, before any API module is loaded. It injects the
two missing enum members directly into the installed `GrantManagementAction` class at startup using
Python's internal enum mutation APIs (`_member_map_`, `_value2member_map_`, `_member_names_`).

A warning is logged at startup when the patch is active:

```
SDK COMPAT PATCH applied: Injected missing GrantManagementAction enum members
into authlete v1.3.0: ['NO_CONTENT', 'NOT_FOUND'].
Remove this patch once upstream SDK is updated.
```

**Removal:** Delete `sdk_compat_patch.py` and remove the two import lines at the top of `main.py`
once the `authlete-python` package ships a version containing these enum members.

---

## License

See [LICENSE](./LICENSE).
