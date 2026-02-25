from fastapi import FastAPI
from api import authorization, token, authorization_decision, metadata

app = FastAPI(title="Authlete Python Reference Server")

app.include_router(authorization_decision.router)
app.include_router(authorization.router)
app.include_router(token.router)
app.include_router(metadata.router)