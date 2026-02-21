import pytest
from httpx import Client

def test_authorization_missing_params(client: Client, target_url: str):
    """
    RFC 6749 Section 4.1.1:
    If the request is missing a required parameter, the authorization server
    should return an error.
    
    Scenario: User hits /api/authorization with NO parameters.
    Expected: 400 Bad Request (The server refuses to process it).
    """
    # 1. Construct the URL
    endpoint = f"{target_url}/api/authorization"
    
    # 2. Execute GET
    response = client.get(endpoint)
    
    # 3. Assert Compliance
    assert response.status_code == 400, \
        f"Expected 400 for missing params, got {response.status_code}. Body: {response.text}"
        
    print(f"\n[Response] Status: {response.status_code}, Type: {response.headers.get('content-type')}")