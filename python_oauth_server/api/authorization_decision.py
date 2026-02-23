from fastapi import APIRouter, Request, Response, Form
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration

from authlete.dto.authorization_issue_request import AuthorizationIssueRequest
from authlete.dto.authorization_fail_request import AuthorizationFailRequest
try:
    from authlete.types.authorization_fail_reason import AuthorizationFailReason
except ModuleNotFoundError:
    from authlete.dto.authorization_fail_reason import AuthorizationFailReason

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.post("/api/authorization/decision")
async def authorization_decision_endpoint(
    request: Request,
    ticket: str = Form(...),
    subject: str = Form(...), # User's subject (username)
    authorized: str = Form(...) # True or False
):
    """
    Mirrors AuthorizationDecisionEndpoint.java.
    Takes the user's login form, tells Authlete if they approved or denied,
    and returns the final redirect (302) to the client with the auth code.
    """
    if authorized == "true":
        # 1. user clicked authorize
        issue_request = AuthorizationIssueRequest()
        issue_request.ticket = ticket
        issue_request.subject = subject # Later, will add password verification first


        # Ask authlete to issue the code
        authlete_res = authlete_api.authorization_issue(issue_request)
        action = authlete_res.action.name if hasattr(authlete_res.action, 'name') else str(authlete_res.action)

        if action == "LOCATION":
            # Sucess, Authlete generated the callback URL with the ?code=xxx attached
            return Response(
                status_code=302,
                headers={"Location": authlete_res.responseContent, "Cache-Control": "no-store"}
            )
        else:
            return Response(content=authlete_res.responseContent, status_code=500)

    else:
        # User clicked deny
        fail_request = AuthorizationFailRequest()
        fail_request.ticket = ticket
        fail_request.reason = AuthorizationFailReason.DENIED

        authlete_res = authlete_api.authorization_fail(fail_request)

        return Response(status_code=302, headers={"Location": authlete_res.responseContent, "Cache-Control": "no-store"})
