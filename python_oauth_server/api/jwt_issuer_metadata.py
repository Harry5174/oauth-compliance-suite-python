from fastapi import APIRouter, Response
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.credential_jwt_issuer_metadata_request import CredentialJwtIssuerMetadataRequest

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

@router.get("/.well-known/jwt-issuer")
async def jwt_issuer_metadata_endpoint():
    """
    SD-JWT Issuer Metadata Endpoint (RFC 9499 / OID4VCI).
    Returns the JWT issuer configuration including signing keys.
    """
    req = CredentialJwtIssuerMetadataRequest()

    res = authlete_api.credentialJwtIssuerMetadata(req)
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