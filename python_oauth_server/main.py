from fastapi import FastAPI
from api import authorization, token

app = FastAPI(title="Authlete Python Reference Server")

app.include_router(authorization.router)
app.include_router(token.router)