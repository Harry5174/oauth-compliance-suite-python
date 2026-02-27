import pytest
from httpx import Client
import re
import base64
import os
import dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")

def test_token_revocation(client: Client, target_url: str):
    """
    Scenario: Client gets a token, revokes it via /api/revocation, 
    and a Resource Server confirms it is no longer active.
    """
    CLIENT_ID = os.getenv("CLIENT_ID") 
    CLIENT_SECRET = os.getenv("CLIENT_SECRET") 
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    
    # -------------------------------------------------------------------------
    # 1. SETUP: Get the Access Token
    # -------------------------------------------------------------------------
    params = {"response_type": "code", "client_id": CLIENT_ID, "scope": "openid", "redirect_uri": REDIRECT_URI}
    init_res = client.get(f"{target_url}/api/authorization", params=params)
    
    ticket = None
    m = re.search(r'name="ticket"\s+value="([^"]+)"', init_res.text)
    if m: ticket = m.group(1)

    if "8080" in target_url:
        form_data = {"loginId": "max", "password": "max", "authorized": "Authorize"}
    else:
        assert ticket is not None
        form_data = {"ticket": ticket, "subject": "max", "password": "max", "authorized": "true"}
    
    decision_res = client.post(f"{target_url}/api/authorization/decision", data=form_data, follow_redirects=False)
    location = decision_res.headers.get("Location", "")
    auth_code = re.search(r'code=([^&]+)', location).group(1)

    encoded_client_creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    token_payload = {"grant_type": "authorization_code", "code": auth_code, "redirect_uri": REDIRECT_URI}
    token_headers = {"Authorization": f"Basic {encoded_client_creds}", "Content-Type": "application/x-www-form-urlencoded"}
    
    token_res = client.post(f"{target_url}/api/token", data=token_payload, headers=token_headers)
    access_token = token_res.json().get("access_token")
    assert access_token is not None
    
    # -------------------------------------------------------------------------
    # 2. TEST: Revoke the Token (RFC 7009)
    # -------------------------------------------------------------------------
    # The client MUST authenticate to the revocation endpoint
    revocation_payload = {"token": access_token}
    
    rev_res = client.post(
        f"{target_url}/api/revocation", 
        data=revocation_payload, 
        headers=token_headers # Reusing the Client Basic Auth headers
    )
    
    print(f"\n[Revocation Status] {rev_res.status_code}")
    assert rev_res.status_code == 200, "Revocation MUST return 200 OK"
    
    # -------------------------------------------------------------------------
    # 3. VERIFICATION: Introspect the Revoked Token
    # -------------------------------------------------------------------------
    RS_CLIENT_ID = os.getenv("RS_CLIENT_ID")
    RS_CLIENT_SECRET = os.getenv("RS_CLIENT_SECRET")
    rs_credentials = base64.b64encode(f"{RS_CLIENT_ID}:{RS_CLIENT_SECRET}".encode()).decode()
    
    introspection_headers = {
        "Authorization": f"Basic {rs_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    intro_payload = {"token": access_token}
    
    intro_res = client.post(f"{target_url}/api/introspection", data=intro_payload, headers=introspection_headers)
    
    assert intro_res.status_code == 200
    intro_data = intro_res.json()
    
    # The ultimate invariant: The token must now be inactive
    assert intro_data.get("active") is False, "Token is still active after revocation!"