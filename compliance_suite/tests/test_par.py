from httpx import Client
import base64
import os
import dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")

def test_pushed_authorization_request(client: Client, target_url: str):
    """
    Scenario: Client securely pushes authorization parameters via a backend 
    POST request before redirecting the user.
    Expected: A 201 Created response containing a `request_uri`.
    """
    CLIENT_ID = os.getenv("CLIENT_ID") 
    CLIENT_SECRET = os.getenv("CLIENT_SECRET") 
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    
    # -------------------------------------------------------------------------
    # 1. SETUP: Prepare the Authorization Parameters
    # -------------------------------------------------------------------------
    par_payload = {
        "response_type": "code", 
        "client_id": CLIENT_ID, 
        "scope": "openid", 
        "redirect_uri": REDIRECT_URI,
        # We can safely push sensitive data like PKCE challenges here
        "code_challenge_method": "S256",
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    }

    # The client MUST authenticate to the PAR endpoint
    encoded_client_creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_client_creds}", 
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # -------------------------------------------------------------------------
    # 2. TEST: Call the Pushed Auth Req Endpoint (RFC 9126)
    # -------------------------------------------------------------------------
    par_res = client.post(f"{target_url}/api/par", data=par_payload, headers=headers)
    
    print(f"\n[PAR Status] {par_res.status_code}")
    print(par_res.text)

    # -------------------------------------------------------------------------
    # 3. PROTOCOL INVARIANTS
    # -------------------------------------------------------------------------
    assert par_res.status_code == 201, "PAR request MUST return 201 Created"
    
    data = par_res.json()
    assert "request_uri" in data, "PAR response MUST contain a 'request_uri'"
    assert "expires_in" in data, "PAR response MUST contain 'expires_in'"
    
    # The URI format is strictly defined by the specification
    assert str(data["request_uri"]).startswith("urn:ietf:params:oauth:request_uri:"), "Invalid request_uri format"