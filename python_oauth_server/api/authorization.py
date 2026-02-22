from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from authlete.api.authlete_api import AuthleteApi
from authlete.dto.authorization_request import AuthorizationRequest
from authlete.conf.authlete_properties_configuration import AuthletePropertiesConfiguration
from authlete.api.authlete_api_impl import AuthleteApiImpl

router = APIRouter()

# 1. Load configuration directly from the Java-style properties file
conf = AuthletePropertiesConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.get("/api/authorization")
async def authorization_endpoint(request: Request):
    """
    The Delegated Protocol Engine Pattern.
    """
    query_string = request.url.query
    
    authlete_req = AuthorizationRequest()
    authlete_req.parameters = query_string
    
    # 2. Call Authlete (SDK automatically uses the Access Token for v3)
    authlete_res = authlete_api.authorization(authlete_req)
    action = authlete_res.action
    
    # 3. Action Dispatcher
    if action == "BAD_REQUEST":
        return Response(
            content=authlete_res.responseContent,
            status_code=400,
            media_type="application/json"
        )
        
    elif action == "INTERACTION":
        # Placeholder for Phase 2
        return Response(content="<html>Login Page Placeholder</html>", status_code=200, media_type="text/html")
        
    elif action == "INTERNAL_SERVER_ERROR":
        return Response(
            content=authlete_res.responseContent,
            status_code=500,
            media_type="application/json"
        )
        
    else:
        return JSONResponse({"error": "server_error", "action": action}, status_code=500)