import pytest
from httpx import Client
import re
import base64
import os
import dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")

def test_userinfo_endpoint(client: Client, target_url: str):
    """
    Scenario: Client completes auth flow, gets an access token, 
    and uses it to retrieve user profile data from /api/userinfo.
    """
    CLIENT_ID = os.getenv("CLIENT_ID") 
    CLIENT_SECRET = os.getenv("CLIENT_SECRET") 
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    
    # --- TEST PARAMETERS ---
    TEST_LOGIN = "max"
    TEST_PASSWORD = "max"
    EXPECTED_SUB = "1003"
    
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
    # 2. TEST: Call the UserInfo Endpoint
    # -------------------------------------------------------------------------
    userinfo_headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_res = client.get(f"{target_url}/api/userinfo", headers=userinfo_headers)
    
    print(f"\n[UserInfo Status] {userinfo_res.status_code}")
    print(userinfo_res.text)
    
    # -------------------------------------------------------------------------
    # 3. PROTOCOL INVARIANTS
    # -------------------------------------------------------------------------
    assert userinfo_res.status_code == 200, "UserInfo request failed"
    
    data = userinfo_res.json()
    assert "sub" in data, "UserInfo response MUST contain a 'sub' claim"
    assert data["sub"] == EXPECTED_SUB, f"Expected subject '{EXPECTED_SUB}', got {data.get('sub')}"