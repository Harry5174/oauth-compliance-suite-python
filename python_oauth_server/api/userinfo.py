import json
from fastapi import APIRouter, Request, Response, Header
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.userinfo_request import UserInfoRequest
from authlete.dto.userinfo_issue_request import UserInfoIssueRequest
from db.user_dao import UserDao

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.api_route("/api/userinfo", methods=["GET", "POST"])
async def userinfo_endpoint(request: Request, authorization: str = Header(None)):
    """
    Serves the user's profile claims based on their access token.
    """
    # 1. Extract the Bearer Token
    if not authorization or not authorization.startswith("Bearer "):
        return Response(status_code=401, content="Missing Bearer Token")
    
    token = authorization.split(" ")[1]

    # 2. Ask Authlete to validate the token
    req = UserInfoRequest()
    req.token = token
    res = authlete_api.userinfo(req)

    action = res.action.name if hasattr(res.action, 'name') else str(res.action)

    if action == "OK":
        subject = res.subject

        # 3. Fetch the real user record from db
        user_record = UserDao.get_by_subject(subject)
        # 4. Populate the standard OIDC claims
        claims = {"sub": subject}

        if user_record:
            # Map database fields to standard OpenID Connect claim names
            claims["name"] = user_record.get("name")
            claims["email"] = user_record.get("email")

        # 5. Issue the Final Response
        issue_req = UserInfoIssueRequest()
        issue_req.token = token
        issue_req.claims = json.dumps(claims)

        issue_res = authlete_api.userinfoIssue(issue_req)
        
        # We must include the headers Authlete provides (like Content-Type)
        return Response(
            content=issue_res.responseContent,
            status_code=200,
            media_type="application/json"
        )
    else:
        # Token is invalid, expired, or missing permissions
        status_code = 400
        if action == "UNAUTHORIZED": status_code = 401
        elif action == "FORBIDDEN": status_code = 403
        elif action == "INTERNAL_SERVER_ERROR": status_code = 500
        
        return Response(
            content=res.responseContent,
            status_code=status_code,
            media_type="application/json"
        )