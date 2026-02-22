import os 
import pytest
import httpx
from typing import Generator

TARGETS = {
    "JAVA" : "http://localhost:8080",
    "PYTHON" : "http://localhost:8000"
}

@pytest.fixture(scope="session")
def target_url() -> str:
    """
    Determines which server to test based on the TARGET env var.
    Defaults to JAVA for establishing the baseline.
    """

    target_env = os.getenv("TARGET", "JAVA").upper()
    if target_env not in TARGETS:
        raise ValueError(f"Invalid target environment: {target_env}. Must be one of {list(TARGETS.keys())}")

    url = TARGETS[target_env]
    print(f"\nTesting target: {target_env} at {url}")
    return url

@pytest.fixture(scope="session")
def client() -> Generator[httpx.Client, None, None]:
    """
    Yields a synchronous HTTP client.
    follow_redirects=False is CRITICAL for OAuth testing because 
    we need to inspect the 'Location' header of 302 responses 
    instead of following them automatically.
    """
    with httpx.Client(follow_redirects=False, timeout=10.0) as client:
        yield client
    