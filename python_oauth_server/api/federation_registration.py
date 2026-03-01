from fastapi import APIRouter, Request, Response
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.federation_registration_request import FederationRegistrationRequest

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.post("/api/federation/register")
async def federation_registration_endpoint(request: Request):
    """
    OpenID Federation Explicit Registration Endpoint.
    Accepts an Entity Statement (JWT) and registers the client if the Trust Chain is valid.
    """
    # 1. Read the raw JWT string from the request body
    body_bytes = await request.body()
    entity_statement = body_bytes.decode('utf-8')

    # 2. Call Authlete's Federation Registration API
    req = FederationRegistrationRequest()
    req.entityConfiguration = entity_statement
    
    res = authlete_api.federationRegistration(req)
    action = res.action.name if hasattr(res.action, 'name') else str(res.action)

    # 3. Handle the Protocol Response
    status_code = 400
    media_type = "application/json"
    
    if action == "CREATED":
        status_code = 201
    elif action == "BAD_REQUEST":
        status_code = 400
    elif action == "INTERNAL_SERVER_ERROR":
        status_code = 500

    return Response(
        content=res.responseContent,
        status_code=status_code,
        media_type=media_type
    )