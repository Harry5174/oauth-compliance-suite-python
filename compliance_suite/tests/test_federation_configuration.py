import pytest
from httpx import Client

def test_openid_federation_configuration(client: Client, target_url: str):
    """
    Scenario: A downstream entity or Trust Anchor requests this IdP's Entity Configuration.
    Expected: A 200 OK returning a signed JWT (application/entity-statement+jwt).
    """
    # -------------------------------------------------------------------------
    # 1. TEST: Call the OpenID Federation Configuration Endpoint
    # -------------------------------------------------------------------------
    fed_res = client.get(f"{target_url}/.well-known/openid-federation")

    # print(f"\n[Federation Config Status] {fed_res.status_code}")
    # print(f"[Content-Type] {fed_res.headers.get('Content-Type')}")
    # print(f"[Payload] {fed_res.text}")

    # -------------------------------------------------------------------------
    # 2. PROTOCOL INVARIANTS
    # -------------------------------------------------------------------------
    assert fed_res.status_code == 200, "Federation Configuration MUST return 200 OK"
    
    # The response MUST be a signed JWT, not standard JSON
    content_type = fed_res.headers.get("Content-Type", "")
    assert "application/entity-statement+jwt" in content_type or "application/jwt" in content_type, \
        f"Invalid Content-Type for Entity Statement: {content_type}"
        
    # A JWT consists of 3 Base64Url encoded parts separated by dots
    body = fed_res.text
    assert len(body.split(".")) == 3, "Response body MUST be a valid JWT string"