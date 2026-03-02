import pytest
from httpx import Client

def test_jwt_issuer_metadata(client: Client, target_url: str):
    """
    Scenario: A client asks the Identity Provider for its SD-JWT Issuer metadata.
    Expected: A 200 OK returning a JSON object detailing the JWT issuer's 
    configuration, including its globally unique issuer URI.
    """
    jwt_meta_res = client.get(f"{target_url}/.well-known/jwt-issuer")
    
    print(f"\n[JWT Issuer Status] {jwt_meta_res.status_code}")
    print(f"[JWT Issuer Response] {jwt_meta_res.text}")
    
    # -------------------------------------------------------------------------
    # PROTOCOL INVARIANTS
    # -------------------------------------------------------------------------
    assert jwt_meta_res.status_code == 200, "JWT Issuer Metadata MUST return 200 OK"
    
    data = jwt_meta_res.json()
    assert "issuer" in data, "Response MUST contain the 'issuer' identifier"
    assert "jwks_uri" in data or "jwks" in data, "Response MUST contain cryptographic key information"