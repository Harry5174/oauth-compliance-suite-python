from fastapi import APIRouter, Request, Response
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.credential_single_issue_request import CredentialSingleIssueRequest
from authlete.dto.credential_issuance_order import CredentialIssuanceOrder

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.post("/api/credential")
async def credential_endpoint(request: Request):
    """
    OID4VCI Credential Endpoint.
    Validates the Access Token and issues a Verifiable Credential.
    """
    # 1. Extract the Bearer token from the Authorization header
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else None

    # 2. Extract the JSON payload
    try:
        request_body = await request.json()
        import json
        request_content = json.dumps(request_body)
    except:
        request_content = ""

    # 3. Call Authlete's Credential Single Issue API
    order = CredentialIssuanceOrder()
    order.credentialPayload = request_content

    req = CredentialSingleIssueRequest()
    req.accessToken = access_token
    req.order = order
    
    res = authlete_api.credentialSingleIssue(req)
    action = res.action.name if hasattr(res.action, 'name') else str(res.action)

    # 4. Handle the Protocol Response
    status_code = 400
    headers = {}
    
    if action == "OK":
        status_code = 200
    elif action == "BAD_REQUEST":
        status_code = 400
    elif action == "UNAUTHORIZED":
        status_code = 401
        # Authlete provides the exact WWW-Authenticate header string we need
        if res.responseContent:
            headers["WWW-Authenticate"] = res.responseContent
            return Response(status_code=status_code, headers=headers)
    elif action == "FORBIDDEN":
        status_code = 403
    elif action == "INTERNAL_SERVER_ERROR":
        status_code = 500

    return Response(
        content=res.responseContent,
        status_code=status_code,
        media_type="application/json",
        headers=headers
    )