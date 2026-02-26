import base64
from fastapi import APIRouter, Request, Response, Header
from urllib.parse import urlencode
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.standard_introspection_request import StandardIntrospectionRequest
from db.resource_server_dao import ResourceServerDao

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.post("/api/introspection")
async def introspection_endpoint(
    request: Request,
    authorization: str = Header(None)
):
    """
    RFC 7662 Introspection Endpoint for Resource Servers.
    """
    # 1. Resource Server Authentication
    if not authorization or not authorization.startswith("Basic "):
        return Response(status_code=401, content="Missing or invalid Basic Auth")
        
    try:
        b64_creds = authorization.split(" ")[1]
        decoded_creds = base64.b64decode(b64_creds).decode()
        rs_id, rs_secret = decoded_creds.split(":", 1)
    except Exception:
        return Response(status_code=401, content="Invalid Basic Auth format")

    # 2. Use the DAO for strict architectural separation
    rs_record = ResourceServerDao.get(rs_id)
    if not rs_record or rs_record.get("secret") != rs_secret:
        return Response(status_code=401, content="Invalid Resource Server credentials")

    # 3. Parse the token payload
    form_data = await request.form()
    parameters = urlencode(form_data)
    
    # 4. Call Authlete
    req = StandardIntrospectionRequest()
    req.parameters = parameters
    
    res = authlete_api.standardIntrospection(req)
    action = res.action.name if hasattr(res.action, 'name') else str(res.action)
    
    # 5. Handle the Protocol Response
    status_code = 200
    if action == "INTERNAL_SERVER_ERROR": status_code = 500
    elif action == "BAD_REQUEST": status_code = 400
        
    return Response(
        content=res.responseContent, 
        status_code=status_code, 
        media_type="application/json"
    )