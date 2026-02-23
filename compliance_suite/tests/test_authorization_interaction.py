import pytest
from httpx import Client

def test_authorization_valid_request_yields_html_form(client: Client, target_url: str):
    """
    Scenario: User hits /api/authorization with VALID parameters.
    Expected: Authlete returns INTERACTION. The server MUST return a 200 OK
    with an HTML body (the login/consent form), pausing the OAuth flow 
    until the user authenticates.
    """
    # Using the exact Client ID and Redirect URI you verified in the Authlete Console
    params = {
        "response_type": "code",
        "client_id": "3345476919",
        "scope": "openid",
        "redirect_uri": "https://oidcdebugger.com/debug"
    }

    endpoint = f"{target_url}/api/authorization"
    response = client.get(endpoint, params=params)
    
    # 1. Invariant: Server must respond with 200 OK (Requires user interaction)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    

    # 2. Invariant: Response must be HTML (The login/consent form)
    assert "text/html" in response.headers.get("content-type", "").lower(), f"Expected text/html, got {response.headers.get('content-type')}"

    # 3. Invariant: The HTML must contain a form for submission
    assert "<form" in response.text.lower(), "HTML response does not contain a form element"