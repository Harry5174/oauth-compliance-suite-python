import pytest
from httpx import Client

def test_federation_registration_endpoint(client: Client, target_url: str):
    """
    Scenario: A foreign entity attempts to register using an Entity Statement.
    Expected: Because we are providing a dummy JWT without a valid trust chain, 
    the IdP should correctly parse the request and return a 400 Bad Request 
    detailing the cryptographic/trust failure.
    """
    # A syntactically valid but cryptographically empty JWT
    dummy_entity_statement = "eyJhbGciOiJub25lIn0.eyJzdWIiOiJ0ZXN0LWFnZW50In0."
    
    # The specification mandates this exact content type for the POST body
    headers = {
        "Content-Type": "application/entity-statement+jwt"
    }
    
    fed_reg_res = client.post(
        f"{target_url}/api/federation/register",
        content=dummy_entity_statement,
        headers=headers
    )
    
    print(f"\n[Fed Reg Status] {fed_reg_res.status_code}")
    print(f"[Fed Reg Response] {fed_reg_res.text}")
    
    # -------------------------------------------------------------------------
    # PROTOCOL INVARIANTS
    # -------------------------------------------------------------------------
    # We expect the server to actively reject invalid trust chains with a 4xx error,
    # NOT crash with a 500 Internal Server Error or 404 Not Found.
    assert fed_reg_res.status_code in [400, 401, 403], "Expected a client error for an invalid entity statement"
    
    data = fed_reg_res.json()
    assert "error" in data, "Response MUST contain an OIDC error payload"