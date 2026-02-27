import base64
from fastapi import APIRouter, Request, Response, Header
from urllib.parse import urlencode
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.revocation_request import RevocationRequest

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.post("/api/revocation")
async def revocation_endpoint(
    request: Request,
    authorization: str = Header(None)
):
    """
    RFC 7009 Token Revocation Endpoint.
    """
    # 1. Extract Client Credentials (RFC 6749 / 7009)
    client_id, client_secret = None, None
    if authorization and authorization.startswith("Basic "):
        try:
            b64_creds = authorization.split(" ")[1]
            decoded_creds = base64.b64decode(b64_creds).decode()
            client_id, client_secret = decoded_creds.split(":", 1)
        except Exception:
            pass # Malformed auth header

    # 2. Parse the application/x-www-form-urlencoded body
    form_data = await request.form()
    parameters = urlencode(form_data)

    # Fallback: OAuth 2.0 allows credentials in the body if Basic Auth isn't used
    if not client_id:
        client_id = form_data.get("client_id")
        client_secret = form_data.get("client_secret")

    # 3. Call Authlete's Revocation API
    req = RevocationRequest()
    req.parameters = parameters
    req.clientId = client_id
    req.clientSecret = client_secret
    
    res = authlete_api.revocation(req)
    action = res.action.name if hasattr(res.action, 'name') else str(res.action)

    # 4. Handle the Protocol State Machine
    status_code = 200
    if action == "INVALID_CLIENT":
        # Client failed authentication
        status_code = 401
    elif action == "BAD_REQUEST":
        # Missing parameters
        status_code = 400
    elif action == "INTERNAL_SERVER_ERROR":
        status_code = 500
        
    return Response(
        content=res.responseContent,
        status_code=status_code,
        media_type="application/json"
    )