from fastapi import APIRouter, Request, Response, Header
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.grant_management_request import GrantManagementRequest
from authlete.types.gm_action import GMAction

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.api_route("/api/gm/{grant_id}", methods=["GET", "DELETE"])
async def grant_management_endpoint(
    request: Request,
    grant_id: str,
    authorization: str = Header(None)
):
    """
    RFC 9356 Grant Management Endpoint.
    Handles querying (GET) and revoking (DELETE) explicit grants.
    """
    # 1. Extract the Bearer Token
    access_token = None
    if authorization and authorization.lower().startswith("bearer "):
        access_token = authorization.split(" ", 1)[1]

    if not access_token:
        return Response(
            status_code=401, 
            content='{"error": "invalid_request", "error_description": "Missing Bearer token"}', 
            media_type="application/json"
        )

    # 2. Determine the RFC 9356 Action
    action = GMAction.QUERY if request.method == "GET" else GMAction.REVOKE

    # 3. Call Authlete's Grant Management API
    req = GrantManagementRequest()
    req.grantId = grant_id
    req.gmAction = action
    req.accessToken = access_token
    
    res = authlete_api.gm(req)
    res_action = res.action.name if hasattr(res.action, 'name') else str(res.action)

    # 4. Handle the Protocol Response
    status_code = 400
    if res_action == "OK":
        status_code = 200
    elif res_action == "NO_CONTENT":
        status_code = 204  # Standard response for a successful DELETE
    elif res_action == "UNAUTHORIZED":
        status_code = 401
    elif res_action == "FORBIDDEN":
        status_code = 403
    elif res_action == "NOT_FOUND":
        status_code = 404
    elif res_action == "INTERNAL_SERVER_ERROR":
        status_code = 500
        
    return Response(
        content=res.responseContent,
        status_code=status_code,
        media_type="application/json"
    )