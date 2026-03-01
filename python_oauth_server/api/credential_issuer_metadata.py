from fastapi import APIRouter, Response
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.credential_issuer_metadata_request import CredentialIssuerMetadataRequest

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.get("/.well-known/openid-credential-issuer")
async def credential_issuer_metadata_endpoint():
    """
    OID4VCI Credential Issuer Metadata Endpoint.
    Returns the configurations of Verifiable Credentials this IdP can issue.
    """
    # 1. Instantiate the empty request DTO
    req = CredentialIssuerMetadataRequest()
    
    # 2. Pass the request object to the SDK
    res = authlete_api.credentialIssuerMetadata(req)
    
    # 3. Process the response
    action = res.action.name if hasattr(res.action, 'name') else str(res.action)

    status_code = 400
    if action == "OK":
        status_code = 200
    elif action == "NOT_FOUND":
        status_code = 404
    elif action == "INTERNAL_SERVER_ERROR":
        status_code = 500
        
    return Response(
        content=res.responseContent,
        status_code=status_code,
        media_type="application/json"
    )