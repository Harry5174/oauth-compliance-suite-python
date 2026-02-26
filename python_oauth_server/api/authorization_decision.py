import json
from fastapi import APIRouter, Request, Response, Form
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from fastapi.templating import Jinja2Templates
from authlete.dto.authorization_issue_request import AuthorizationIssueRequest
from authlete.dto.authorization_fail_request import AuthorizationFailRequest
try:
    from authlete.types.authorization_fail_reason import AuthorizationFailReason
except ModuleNotFoundError:
    from authlete.dto.authorization_fail_reason import AuthorizationFailReason

import json

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)
templates = Jinja2Templates(directory="templates")

# Updated Mock Database
MOCK_USERS = {
    "john": {"password": "john", "sub": "1001"},
    "jane": {"password": "jane", "sub": "1002"},
    "max":  {"password": "max",  "sub": "1003"}
}

@router.post("/api/authorization/decision")
async def authorization_decision_endpoint(
    request: Request,
    ticket: str = Form(...),
    subject: str = Form(None),
    password: str = Form(None),
    authorized: str = Form(...)
):
    if authorized == "true":
        
        # Look up user record
        user_record = MOCK_USERS.get(subject)

        # 1. AUTHENTICATION CHECK
        if not user_record or user_record['password'] != password:
            # Match Java Behavior: Abort the flow immediately.
            fail_request = AuthorizationFailRequest()
            fail_request.ticket = ticket
            fail_request.reason = AuthorizationFailReason.NOT_AUTHENTICATED
            
            authlete_res = authlete_api.authorizationFail(fail_request)
            return Response(
                status_code=302, 
                headers={"Location": authlete_res.responseContent, "Cache-Control": "no-store"}
            )

        # 2. AUTHORIZATION (The Happy Path)
        issue_request = AuthorizationIssueRequest()
        issue_request.ticket = ticket

        # Injecting the internal database ID, Same as java-oauth server
        issue_request.subject = user_record['sub']

        # Ask authlete to issue the code
        authlete_res = authlete_api.authorizationIssue(issue_request)
        action = authlete_res.action.name if hasattr(authlete_res.action, 'name') else str(authlete_res.action)

        if action == "LOCATION":
            # Sucess, Authlete generated the callback URL with the ?code=xxx attached
            return Response(
                status_code=302,
                headers={"Location": authlete_res.responseContent, "Cache-Control": "no-store"}
            )
        else:
            return Response(content=json.dumps(authlete_res, indent=4), status_code=500)

    else:
        # 3. USER DENIED CONSENT
        fail_request = AuthorizationFailRequest()
        fail_request.ticket = ticket
        fail_request.reason = AuthorizationFailReason.DENIED

        authlete_res = authlete_api.authorizationFail(fail_request)
        return Response(status_code=302, headers={"Location": authlete_res.responseContent, "Cache-Control": "no-store"})