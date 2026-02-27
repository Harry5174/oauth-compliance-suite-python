import pytest
from httpx import Client
import re
import os

def test_authorization_decision_invalid_credentials_protocol_failure(client: Client, target_url: str):
    """
    Scenario: User submits the interaction form with a BAD password.
    Expected (Java Reference Behavior): The server aborts the flow and 
    issues a 302 redirect back to the client with an error parameter.
    """
    # 1. Start the flow
    params = {
        "response_type": "code",
        "client_id": "3345476919", 
        "scope": "openid",
        "redirect_uri": "https://oidcdebugger.com/debug"
    }
    init_res = client.get(f"{target_url}/api/authorization", params=params)
    assert init_res.status_code == 200
    
    # 2. Extract Ticket
    ticket = None
    m = re.search(r'name="ticket"\s+value="([^"]+)"', init_res.text)
    if m:
        ticket = m.group(1)

    # 3. Build Payload
    if "8080" in target_url:
        form_data = {"loginId": "john", "password": "wrongpassword123", "authorized": "Authorize"}
    else:
        assert ticket is not None, "Python port requires a ticket"
        form_data = {"ticket": ticket, "subject": "john", "password": "wrongpassword123", "authorized": "true"}
    
    # 4. Execute the Decision
    decision_res = client.post(f"{target_url}/api/authorization/decision", data=form_data, follow_redirects=False)
    
    # 5. The Protocol Invariants
    assert decision_res.status_code == 302, \
        f"Protocol Failure: Expected 302 redirect on bad credentials, got {decision_res.status_code}"
    
    location = decision_res.headers.get("Location", "")
    assert "code=" not in location, "Security Failure: Issued auth code for bad credentials."
    assert "error=" in location, "Protocol Failure: Redirected without an OAuth error parameter."

def test_authorization_decision_form_post_mode(client: Client, target_url: str):
    """
    Scenario: Client requests an id_token and code via form_post response mode.
    Expected: The IdP returns a 200 OK with an HTML auto-submit form (FORM action).
    """
    CLIENT_ID = os.getenv("CLIENT_ID") 
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    
    # Notice we are asking for form_post and id_token code
    params = {
        "response_type": "id_token code", 
        "response_mode": "form_post",
        "client_id": CLIENT_ID, 
        "scope": "openid", 
        "redirect_uri": REDIRECT_URI,
        "nonce": "random_nonce_123" # Required for id_token flows
    }
    
    init_res = client.get(f"{target_url}/api/authorization", params=params)
    
    ticket = None
    m = re.search(r'name="ticket"\s+value="([^"]+)"', init_res.text)
    if m: ticket = m.group(1)

    if "8080" in target_url:
        form_data = {"loginId": "max", "password": "max", "authorized": "Authorize"}
    else:
        assert ticket is not None, "Python port requires a ticket"
        form_data = {"ticket": ticket, "subject": "max", "password": "max", "authorized": "true"}
    
    decision_res = client.post(f"{target_url}/api/authorization/decision", data=form_data, follow_redirects=False)
    
    # If the server correctly handles the FORM action, it should return a 200 OK with HTML
    assert decision_res.status_code == 200
    assert "text/html" in decision_res.headers.get("Content-Type", "")
    assert 'onload="javascript:document.forms[0].submit()"' in decision_res.text