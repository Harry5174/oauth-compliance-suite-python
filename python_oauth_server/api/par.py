import base64
from fastapi import APIRouter, Request, Response, Header
from urllib.parse import urlencode
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.pushed_auth_req_request import PushedAuthReqRequest

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.post("/api/par")
async def pushed_authorization_request_endpoint(
    request: Request,
    authorization: str = Header(None)
):
    """
    RFC 9126 Pushed Authorization Requests (PAR) Endpoint.
    """
    # 1. Extract Client Credentials
    client_id, client_secret = None, None
    if authorization and authorization.startswith("Basic "):
        try:
            b64_creds = authorization.split(" ")[1]
            decoded_creds = base64.b64decode(b64_creds).decode()
            client_id, client_secret = decoded_creds.split(":", 1)
        except Exception:
            pass 

    # 2. Parse the body parameters
    form_data = await request.form()
    parameters = urlencode(form_data)

    # Fallback for credentials in the request body
    if not client_id:
        client_id = form_data.get("client_id")
        client_secret = form_data.get("client_secret")

    # 3. Call Authlete's PAR API
    req = PushedAuthReqRequest()
    req.parameters = parameters
    req.clientId = client_id
    req.clientSecret = client_secret
    
    res = authlete_api.pushAuthorizationRequest(req)
    action = res.action.name if hasattr(res.action, 'name') else str(res.action)

    # 4. Handle the Protocol Response
    status_code = 400
    if action == "CREATED":
        status_code = 201
    elif action == "UNAUTHORIZED":
        status_code = 401
    elif action == "FORBIDDEN":
        status_code = 403
    elif action == "INTERNAL_SERVER_ERROR":
        status_code = 500
        
    return Response(
        content=res.responseContent,
        status_code=status_code,
        media_type="application/json"
    )