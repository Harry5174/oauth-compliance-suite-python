from fastapi import APIRouter, Request, Response
from urllib.parse import urlencode
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_properties_configuration import AuthletePropertiesConfiguration
from authlete.dto.token_request import TokenRequest

router = APIRouter()
conf = AuthletePropertiesConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.post("/api/token")
async def token_endpoint(request: Request):
    """
    Complete Action Dispatcher for the Token Exchange Endpoint.
    """
    # Token endpoint is strictly POST Form Data
    form_data = await request.form()
    parameters = urlencode(form_data)
    
    # Extract Basic Auth from headers if the client is authenticating that way
    auth_header = request.headers.get("Authorization")
    client_id, client_secret = None, None
    if auth_header and auth_header.lower().startswith("basic "):
        import base64
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            client_id, client_secret = decoded.split(":", 1)
        except Exception:
            pass # Malformed header, Authlete will reject it anyway

    authlete_req = TokenRequest()
    authlete_req.parameters = parameters
    authlete_req.clientId = client_id
    authlete_req.clientSecret = client_secret
    
    authlete_res = authlete_api.token(authlete_req)
    action = authlete_res.action.name if hasattr(authlete_res.action, 'name') else str(authlete_res.action)

    # Standard OAuth Error Headers
    no_cache_headers = {"Cache-Control": "no-store", "Pragma": "no-cache"}

    if action == "OK":
        return Response(content=authlete_res.responseContent, status_code=200, media_type="application/json", headers=no_cache_headers)
    elif action == "INVALID_CLIENT":
        # 401 Unauthorized for bad client credentials
        return Response(content=authlete_res.responseContent, status_code=401, media_type="application/json", headers={"WWW-Authenticate": "Basic realm=\"Authlete\""})
    elif action == "BAD_REQUEST":
        return Response(content=authlete_res.responseContent, status_code=400, media_type="application/json", headers=no_cache_headers)
    elif action == "PASSWORD":
        # Resource Owner Password Credentials flow - skipping implementation for now as it's deprecated
        return Response(content='{"error":"unsupported_grant_type"}', status_code=400, media_type="application/json", headers=no_cache_headers)
    else: # INTERNAL_SERVER_ERROR
        return Response(content=authlete_res.responseContent, status_code=500, media_type="application/json", headers=no_cache_headers)