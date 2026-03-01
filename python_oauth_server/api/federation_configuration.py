from fastapi import APIRouter, Response
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.federation_configuration_request import FederationConfigurationRequest

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.get("/.well-known/openid-federation")
async def federation_configuration_endpoint():
    """
    OpenID Federation 1.0 Entity Configuration Endpoint.
    Returns a signed JWT representing this Identity Provider's trust metadata.
    """
    # 1. Prepare the request (No parameters required for the default IdP configuration)
    req = FederationConfigurationRequest()
    
    # 2. Call Authlete's Federation Configuration API
    res = authlete_api.federationConfiguration(req)
    action = res.action.name if hasattr(res.action, 'name') else str(res.action)

    # 3. Handle the Protocol Response
    status_code = 400
    media_type = "application/json"
    
    if action == "OK":
        status_code = 200
        # The specification STRICTLY requires this content type
        media_type = "application/entity-statement+jwt"
    elif action == "NOT_FOUND":
        status_code = 404
    elif action == "INTERNAL_SERVER_ERROR":
        status_code = 500

    return Response(
        content=res.responseContent,
        status_code=status_code,
        media_type=media_type
    )