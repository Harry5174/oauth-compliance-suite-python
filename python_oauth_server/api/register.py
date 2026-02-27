from fastapi import APIRouter, Request, Response
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.client_registration_request import ClientRegistrationRequest

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.post("/api/register")
async def dynamic_client_registration_endpoint(request: Request):
    """
    RFC 7591 Dynamic Client Registration Endpoint.
    """
    # 1. Read the raw JSON payload from the request body
    body_bytes = await request.body()
    json_payload = body_bytes.decode('utf-8')

    # 2. Call Authlete's Client Registration API
    req = ClientRegistrationRequest()
    req.json = json_payload

    # Optional: If you restricted registration using an Initial Access Token, 
    # you would extract the Bearer token from the Authorization header and set req.token here. Since java server was accepting without initial Access Token, we are not adding it here.

    res = authlete_api.dynamicClientRegister(req)
    action = res.action.name if hasattr(res.action, 'name') else str(res.action)

    # 3. Handle the Protocol Response
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