import pytest
from httpx import Client
import re

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