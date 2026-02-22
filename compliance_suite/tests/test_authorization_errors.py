import pytest
from httpx import Client


def test_missing_client_id(client: Client, target_url: str):
    """
    Scenario: User hits /api/authorization with NO client_id.
    Expected: 400 Bad Request (The server refuses to process it).
    """
    # provide response_type but omit client_id
    params =  {"response_type" : "code"}

    # 1. Construct the URL
    endpoint = f"{target_url}/api/authorization"
    
    # 2. Execute GET
    response = client.get(endpoint, params=params)
    
    # 3. Assert Compliance
    assert response.status_code == 400
    # The Java server typically returns a JSON error from Authlete for this
    assert "application/json" in response.headers.get("content-type", "").lower()
        
    data = response.json()
    assert "error" in data
    assert data["error"] == "invalid_client"

def test_unsupported_response_type(client: Client, target_url: str):
    """
    Scenario: User hits /api/authorization with a fake client_id.
    Expected: Even if the response_type is garbage, the server must fail 
    early with 'invalid_client' before evaluating the response_type.
    """

    # provide response_type but omit client_id
    params =  {
        "client_id" : "test_client",
        "response_type" : "invalid_response_type" 
    }


    # 1. Construct the URL
    endpoint = f"{target_url}/api/authorization"
    
    # 2. Execute GET
    response = client.get(endpoint, params=params)
    
    # 3. Assert Compliance
    assert response.status_code == 400
    # The Java server typically returns a JSON error from Authlete for this
    assert "application/json" in response.headers.get("content-type", "").lower()
        
    data = response.json()
    assert "error" in data
    assert data["error"] == "invalid_client"