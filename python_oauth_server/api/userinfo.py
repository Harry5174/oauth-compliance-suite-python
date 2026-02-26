import json
from fastapi import APIRouter, Request, Response, Header
from authlete.api.authlete_api_impl import AuthleteApiImpl
from authlete.conf.authlete_ini_configuration import AuthleteIniConfiguration
from authlete.dto.user_info_request import UserInfoRequest
from authlete.dto.user_info_issue_request import UserInfoIssueRequest

router = APIRouter()
conf = AuthleteIniConfiguration("authlete.properties")
authlete_api = AuthleteApiImpl(conf)

