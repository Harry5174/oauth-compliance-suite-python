import pytest
from httpx import Client

def test_credential_issuer_metadata(client: Client, target_url: str):
    """
    Scenario: A client asks the Identity Provider what types of Verifiable 
    Credentials it is capable of issuing.
    Expected: A 200 OK returning a JSON object detailing supported VC formats.
    """
    vc_meta_res = client.get(f"{target_url}/.well-known/openid-credential-issuer")
    
    print(f"\n[VC Metadata Status] {vc_meta_res.status_code}")
    print(f"[VC Metadata Response] {vc_meta_res.text}")
    # -------------------------------------------------------------------------
    # PROTOCOL INVARIANTS
    # -------------------------------------------------------------------------
    assert vc_meta_res.status_code == 200, "Credential Issuer Metadata MUST return 200 OK"
    
    data = vc_meta_res.json()
    assert "credential_issuer" in data, "Response MUST contain the 'credential_issuer' identifier"
    assert "credential_configurations_supported" in data, "Response MUST list 'credential_configurations_supported'"