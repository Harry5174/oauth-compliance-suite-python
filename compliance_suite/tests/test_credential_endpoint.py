import pytest
from httpx import Client

def test_credential_endpoint_unauthorized(client: Client, target_url: str):
    """
    Scenario: A client requests a Verifiable Credential but provides an invalid
    Access Token.
    Expected: The Credential Endpoint MUST reject the request with a 401 Unauthorized
    and standard OIDC error formatting.
    """
    # Standard format requested by the client
    payload = {
        "format": "jwt_vc_json",
        "credential_definition": {
            "type": [
                "VerifiableCredential",
                "UniversityDegreeCredential"
            ]
        }
    }
    
    # Intentionally passing a fake access token
    headers = {
        "Authorization": "Bearer invalid_dummy_token_123",
        "Content-Type": "application/json"
    }
    
    cred_res = client.post(
        f"{target_url}/api/credential",
        json=payload,
        headers=headers
    )
    
    print(f"\n[Credential Status] {cred_res.status_code}")
    print(f"[Credential Response] {cred_res.text}")
    
    # -------------------------------------------------------------------------
    # PROTOCOL INVARIANTS
    # -------------------------------------------------------------------------
    assert cred_res.status_code == 401, "Credential Endpoint MUST return 401 for invalid tokens"
    
    if cred_res.text:
        data = cred_res.json()
        assert "error" in data, "Response MUST contain an error code"
        assert data["error"] == "invalid_token", "Error code MUST strictly be 'invalid_token'"
    else:
        # If the body is empty, the error MUST be in the WWW-Authenticate header (RFC 6750)
        www_auth = cred_res.headers.get("WWW-Authenticate", "")
        assert "error=\"invalid_token\"" in www_auth, "Error MUST be 'invalid_token' in WWW-Authenticate header"