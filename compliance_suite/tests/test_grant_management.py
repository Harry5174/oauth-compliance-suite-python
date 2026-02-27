import pytest
from httpx import Client
import base64
import os
import re
import dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")

def test_grant_management_endpoint(client: Client, target_url: str):
    """
    Scenario: A client creates a grant, queries it, explicitly revokes it, 
    and verifies it has been destroyed.
    """
    CLIENT_ID = os.getenv("CLIENT_ID") 
    CLIENT_SECRET = os.getenv("CLIENT_SECRET") 
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    
    # -------------------------------------------------------------------------
    # 1. SETUP: Request a Grant ID and the Query Scope
    # -------------------------------------------------------------------------
    params = {
        "response_type": "code", 
        "client_id": CLIENT_ID, 
        "scope": "openid grant_management_query grant_management_revoke", # Added revoke scope just in case
        "redirect_uri": REDIRECT_URI,
        "grant_management_action": "create"
    }
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

    encoded_creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    token_payload = {"grant_type": "authorization_code", "code": auth_code, "redirect_uri": REDIRECT_URI}
    token_headers = {"Authorization": f"Basic {encoded_creds}", "Content-Type": "application/x-www-form-urlencoded"}
    
    token_res = client.post(f"{target_url}/api/token", data=token_payload, headers=token_headers)
    token_data = token_res.json()
    
    access_token = token_data.get("access_token")
    grant_id = token_data.get("grant_id")
    
    assert access_token is not None
    assert grant_id is not None
    
    gm_headers = {"Authorization": f"Bearer {access_token}"}

    # -------------------------------------------------------------------------
    # 2. TEST: Query the Grant (GET)
    # -------------------------------------------------------------------------
    gm_get_res = client.get(f"{target_url}/api/gm/{grant_id}", headers=gm_headers)
    print(f"\n[Grant Query Status] {gm_get_res.status_code}")
    assert gm_get_res.status_code == 200, "Expected a 200 OK for a valid grant query"

    # -------------------------------------------------------------------------
    # 3. TEST: Revoke the Grant (DELETE)
    # -------------------------------------------------------------------------
    gm_del_res = client.delete(f"{target_url}/api/gm/{grant_id}", headers=gm_headers)
    print(f"[Grant Revocation Status] {gm_del_res.status_code}")
    
    # RFC 9356 dictates a 204 No Content for a successful deletion
    assert gm_del_res.status_code == 204, f"Expected 204 No Content, got {gm_del_res.status_code}"

    # -------------------------------------------------------------------------
    # 4. VERIFY: Ensure the grant is actually gone
    # -------------------------------------------------------------------------
    gm_verify_res = client.get(f"{target_url}/api/gm/{grant_id}", headers=gm_headers)
    print(f"[Post-Revocation Query Status] {gm_verify_res.status_code}")
    
    # The IdP should return an error if we try to query a destroyed grant
    assert gm_verify_res.status_code in [401, 403, 404], "Grant is still active after deletion!"