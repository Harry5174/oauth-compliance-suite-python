import pytest
from httpx import Client
import re
import base64
import os
import dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")

def test_introspection_endpoint(client: Client, target_url: str):
    """
    Scenario: A Resource Server checks if an access token is valid 
    by sending it to the /api/introspection endpoint.
    Expected: A 200 OK containing {"active": true} and token metadata.
    """
    CLIENT_ID = os.getenv("CLIENT_ID") 
    CLIENT_SECRET = os.getenv("CLIENT_SECRET") 
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    
    # --- TEST PARAMETERS ---
    TEST_LOGIN = "max"
    TEST_PASSWORD = "max"
    
    # -------------------------------------------------------------------------
    # 1. SETUP: Get the Access Token
    # -------------------------------------------------------------------------
    params = {"response_type": "code", "client_id": CLIENT_ID, "scope": "openid", "redirect_uri": REDIRECT_URI}
    init_res = client.get(f"{target_url}/api/authorization", params=params)
    
    ticket = None
    m = re.search(r'name="ticket"\s+value="([^"]+)"', init_res.text)
    if m: ticket = m.group(1)

    if "8080" in target_url:
        form_data = {"loginId": TEST_LOGIN, "password": TEST_PASSWORD, "authorized": "Authorize"}
    else:
        assert ticket is not None
        form_data = {"ticket": ticket, "subject": TEST_LOGIN, "password": TEST_PASSWORD, "authorized": "true"}
    
    decision_res = client.post(f"{target_url}/api/authorization/decision", data=form_data, follow_redirects=False)
    
    location = decision_res.headers.get("Location", "")
    auth_code = re.search(r'code=([^&]+)', location).group(1)

    encoded_credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    token_payload = {"grant_type": "authorization_code", "code": auth_code, "redirect_uri": REDIRECT_URI}
    token_headers = {"Authorization": f"Basic {encoded_credentials}", "Content-Type": "application/x-www-form-urlencoded"}
    
    token_res = client.post(f"{target_url}/api/token", data=token_payload, headers=token_headers)
    access_token = token_res.json().get("access_token")
    
    assert access_token is not None, "Failed to retrieve access token for setup"

    # -------------------------------------------------------------------------
    # 2. TEST: Call the Introspection Endpoint
    # -------------------------------------------------------------------------
    # Introspection endpoints require authentication from the RESOURCE SERVER
    RS_CLIENT_ID = "rs0" 
    RS_CLIENT_SECRET = "rs0-secret"

    rs_credentials = base64.b64encode(f"{RS_CLIENT_ID}:{RS_CLIENT_SECRET}".encode()).decode()
    introspection_headers = {
        "Authorization": f"Basic {rs_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    introspection_payload = {
        "token": access_token
    }
    
    intro_res = client.post(f"{target_url}/api/introspection", data=introspection_payload, headers=introspection_headers)
    
    print(f"\n[Introspection Status] {intro_res.status_code}")
    print(intro_res.text)
    
    # -------------------------------------------------------------------------
    # 3. PROTOCOL INVARIANTS (RFC 7662)
    # -------------------------------------------------------------------------
    assert intro_res.status_code == 200, "Introspection request failed"
    
    data = intro_res.json()
    assert "active" in data, "Introspection response MUST contain an 'active' boolean"
    assert data["active"] is True, "Token should be reported as active"
    
    # If active, it should return the client_id it was issued to
    assert "client_id" in data, "Active token response must include client_id"
    assert str(data["client_id"]) == CLIENT_ID