import json
from fastapi import APIRouter, Response
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.get("/.well-known/openid-configuration")
async def discovery_endpoint():
    """
    Serves the OpenID Provider Configuration Document.
    """
    res = authlete_api.getServiceConfiguration()
    
    # Parse the raw string into a Python dictionary
    # FastAPI will automatically serialize this back to application/json
    return json.loads(res)

@router.get("/api/jwks")
async def jwks_endpoint():
    """
    Serves the JSON Web Key Set (public keys).
    """
    res = authlete_api.getServiceJwks()
    
    if not res:
        return Response(status_code=204)
        
    # Parse the raw string into a Python dictionary
    return json.loads(res)