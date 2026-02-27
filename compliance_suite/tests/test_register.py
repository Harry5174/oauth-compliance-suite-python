from httpx import Client

def test_dynamic_client_registration(client: Client, target_url: str):
    """
    Scenario: A new application dynamically registers itself with the IdP.
    Expected: A 201 Created response containing a new client_id and client_secret.
    """
    # -------------------------------------------------------------------------
    # 1. SETUP: Prepare the client metadata (RFC 7591)
    # -------------------------------------------------------------------------
    registration_payload = {
        "client_name": "Dynamic AI Agent 007",
        "redirect_uris": ["https://agent.local/callback"],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "scope": "openid profile email"
    }

    # -------------------------------------------------------------------------
    # 2. TEST: Call the Dynamic Client Registration Endpoint
    # -------------------------------------------------------------------------
    # Open dynamic registration usually does not require an initial access token
    reg_res = client.post(
        f"{target_url}/api/register", 
        json=registration_payload
    )
    
    print(f"\n[Registration Status] {reg_res.status_code}")
    print(reg_res.text)

    # -------------------------------------------------------------------------
    # 3. PROTOCOL INVARIANTS
    # -------------------------------------------------------------------------
    assert reg_res.status_code == 201, "Registration MUST return 201 Created"
    
    data = reg_res.json()
    assert "client_id" in data, "Response MUST contain a 'client_id'"
    assert "client_secret" in data, "Response MUST contain a 'client_secret'"
    
    # The server should echo back the registered metadata
    assert data.get("client_name") == "Dynamic AI Agent 007", "Client name mismatch"
    assert "https://agent.local/callback" in data.get("redirect_uris", []), "Redirect URI missing"