from fastapi import FastAPI
from api import authorization, token, authorization_decision, metadata, userinfo, introspection, revocation, par, register, gm, federation_configuration, federation_registration

app = FastAPI(title="Authlete Python Reference Server")

app.include_router(authorization_decision.router)
app.include_router(authorization.router)
app.include_router(token.router)
app.include_router(metadata.router)
app.include_router(userinfo.router)
app.include_router(introspection.router)
app.include_router(revocation.router)
app.include_router(par.router)
app.include_router(register.router)
app.include_router(gm.router)
app.include_router(federation_configuration.router)
app.include_router(federation_registration.router)
