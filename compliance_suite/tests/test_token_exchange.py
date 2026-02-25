import pytest
from httpx import Client
import re
import base64
import os
import dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")

def test_successful_token_exchange(client: Client, target_url: str):
    """
    Scenario: Client completes the authorization flow, receives a code, 
    and exchanges it for an access token via the /api/token endpoint.
    """
    # --- SETUP ---
    CLIENT_ID = os.getenv("CLIENT_ID") 
    CLIENT_SECRET = os.getenv("CLIENT_SECRET") 
    REDIRECT_URI = os.getenv("REDIRECT_URI")

    # -------------------------------------------------------------------------
    # PART 1: The Front-Channel (Get the Code)
    # -------------------------------------------------------------------------
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID, 
        "scope": "openid",
        "redirect_uri": REDIRECT_URI
    }
    init_res = client.get(f"{target_url}/api/authorization", params=params)
    assert init_res.status_code == 200
    
    ticket = None
    m = re.search(r'name="ticket"\s+value="([^"]+)"', init_res.text)
    if m: ticket = m.group(1)

    # Use the 'john' credentials you just standardized
    if "8080" in target_url:
        form_data = {"loginId": "john", "password": "john", "authorized": "Authorize"}
    else:
        assert ticket is not None, "Ticket missing in Python DOM"
        form_data = {"ticket": ticket, "subject": "john", "password": "john", "authorized": "true"}
    
    decision_res = client.post(f"{target_url}/api/authorization/decision", data=form_data, follow_redirects=False)
    assert decision_res.status_code == 302
    
    location = decision_res.headers.get("Location", "")
    code_match = re.search(r'code=([^&]+)', location)
    assert code_match is not None, f"Failed to get authorization code. Location: {location}"
    auth_code = code_match.group(1)

    # -------------------------------------------------------------------------
    # PART 2: The Back-Channel (Exchange the Code)
    # -------------------------------------------------------------------------
    
    # Create the Basic Auth Header
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # RFC 6749 Token Request Payload
    token_payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI
    }
    
    token_res = client.post(f"{target_url}/api/token", data=token_payload, headers=headers)

    # -------------------------------------------------------------------------
    # PART 3: The Protocol Invariants
    # -------------------------------------------------------------------------
    assert token_res.status_code == 200, f"Token exchange failed: {token_res.text}"
    
    json_response = token_res.json()
    assert "access_token" in json_response, "Response missing access_token"
    assert "id_token" in json_response, "Response missing id_token"