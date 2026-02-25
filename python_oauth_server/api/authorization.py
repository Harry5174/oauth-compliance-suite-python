from fastapi import APIRouter, Request, Response
from urllib.parse import urlencode
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.authorization_request import AuthorizationRequest
from fastapi.templating import Jinja2Templates
import json

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

templates = Jinja2Templates(directory="templates")

# RFC 6749: MUST support GET and POST
@router.api_route("/api/authorization", methods=["GET", "POST"])
async def authorization_endpoint(request: Request):
    """
    Complete Action Dispatcher for the Authorization Endpoint.
    """
    # 1. Extract Parameters (Handle both GET query and POST form)
    if request.method == "GET":
        parameters = request.url.query
    else:
        form_data = await request.form()
        parameters = urlencode(form_data) # Convert form to URL-encoded string

    # 2. Call Authlete
    authlete_req = AuthorizationRequest()
    authlete_req.parameters = parameters
    authlete_res = authlete_api.authorization(authlete_req)

    print("ticket before authorization: ", json.dumps(authlete_res.ticket, indent=4))    
    
    # In authlete-python, the action is an Enum. We get its name.
    action = authlete_res.action.name if hasattr(authlete_res.action, 'name') else str(authlete_res.action)

    # 3. The Complete Action Switch (Mirroring Java Reference)
    if action == "BAD_REQUEST":
        return Response(
            content=authlete_res.responseContent,
            status_code=400,
            media_type="application/json",
            headers={"Cache-Control": "no-store", "Pragma": "no-cache"}
        )
        
    elif action == "INTERACTION":
        # TODO: Phase 2 - Render Jinja2 Login Form, save ticket to session
        return templates.TemplateResponse(
            "authorization.html",
            {"request": request, "ticket": authlete_res.ticket}
        )
        
    elif action == "LOCATION":
        # 302 Redirect back to the client application
        return Response(
            status_code=302,
            headers={"Location": authlete_res.responseContent, "Cache-Control": "no-store"}
        )
        
    elif action == "NO_INTERACTION":
        # Client requested prompt=none, but user is not logged in.
        # Authlete generates the redirect back to the client with an error.
        return Response(
            status_code=302,
            headers={"Location": authlete_res.responseContent, "Cache-Control": "no-store"}
        )
        
    else: # INTERNAL_SERVER_ERROR
        return Response(
            content=authlete_res.responseContent,
            status_code=500,
            media_type="application/json"
        )