import pytest
from httpx import Client

def test_discovery_endpoint(client: Client, target_url: str):
    """
    Scenario: Client requests the OpenID Provider Configuration Document.
    Expected: A 200 OK containing a JSON object with strictly required metadata fields.
    """
    res = client.get(f"{target_url}/.well-known/openid-configuration")
    
    print(f"\n[Discovery Status] {res.status_code}")
    assert res.status_code == 200, f"Discovery endpoint failed: {res.text}"
    
    data = res.json()

    # According to OpenID Connect Discovery 1.0, these are strictly REQUIRED
    assert "issuer" in data, "Missing issuer"
    assert "authorization_endpoint" in data, "Missing authorization_endpoint"
    assert "jwks_uri" in data, "Missing jwks_uri"
    assert "response_types_supported" in data, "Missing response_types_supported"
    assert "subject_types_supported" in data, "Missing subject_types_supported"
    assert "id_token_signing_alg_values_supported" in data, "Missing id_token_signing_alg_values_supported"
    
    # We should also expect our token endpoint to be advertised
    assert "token_endpoint" in data, "Missing token_endpoint"

def test_jwks_endpoint(client: Client, target_url: str):
    """
    Scenario: Client requests the JSON Web Key Set to verify token signatures.
    Expected: A 200 OK containing a JSON object with a 'keys' array.
    """
    res = client.get(f"{target_url}/api/jwks")
    
    print(f"\n[JWKS Status] {res.status_code}")
    assert res.status_code == 200, f"JWKS endpoint failed: {res.text}"
    
    data = res.json()

    # RFC 7517 JSON Web Key (JWK) formatting
    assert "keys" in data, "JWKS response must contain a 'keys' array"
    assert isinstance(data["keys"], list), "'keys' must be a JSON array"
    assert len(data["keys"]) > 0, "JWKS should contain at least one public key"
    
    # Verify the structure of the first key
    first_key = data["keys"][0]
    assert "kty" in first_key, "Key must have a key type (kty), usually 'RSA' or 'EC'"
    assert "use" in first_key, "Key should define its use (e.g., 'sig' for signature)"
    assert "kid" in first_key, "Key should have a Key ID (kid) for cache rotation"