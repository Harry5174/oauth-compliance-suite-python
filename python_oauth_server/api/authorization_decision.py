import json
import time
from fastapi import APIRouter, Request, Response, Form
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from fastapi.templating import Jinja2Templates
from authlete.dto.authorization_issue_request import AuthorizationIssueRequest
from authlete.dto.authorization_fail_request import AuthorizationFailRequest
from db.user_dao import UserDao
try:
    from authlete.types.authorization_fail_reason import AuthorizationFailReason
except ModuleNotFoundError:
    from authlete.dto.authorization_fail_reason import AuthorizationFailReason

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)
templates = Jinja2Templates(directory="templates")

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
        user_record = UserDao.get_by_login_id(subject)

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
        issue_request.subject = user_record['subject']

        # 4. FIX: ADD AUTH_TIME (Current time in seconds since epoch)
        issue_request.authTime = int(time.time())

        # Ask authlete to issue the code
        authlete_res = authlete_api.authorizationIssue(issue_request)
        action = authlete_res.action.name if hasattr(authlete_res.action, 'name') else str(authlete_res.action)

        # Handle the OIDC state machine
        if action == "LOCATION":
            # Standard Authorization Code flow
            return Response(
                status_code=302, 
                headers={"Location": authlete_res.responseContent, "Cache-Control": "no-store"}
            )
        elif action == "FORM":
            # Hybrid Flow or form_post response mode
            return Response(
                content=authlete_res.responseContent,
                status_code=200,
                media_type="text/html;charset=UTF-8",
                headers={"Cache-Control": "no-store"}
            )
        else:
            # Fallback for INTERNAL_SERVER_ERROR or unexpected actions
            # FIX: Ensure we return the string content, not the Python object
            return Response(
                content=authlete_res.responseContent, 
                status_code=500,
                media_type="application/json"
            )

    else:
        # 3. USER DENIED CONSENT
        fail_request = AuthorizationFailRequest()
        fail_request.ticket = ticket
        fail_request.reason = AuthorizationFailReason.DENIED

        authlete_res = authlete_api.authorizationFail(fail_request)
        return Response(status_code=302, headers={"Location": authlete_res.responseContent, "Cache-Control": "no-store"})