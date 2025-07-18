# project import
from src.routers import crm_document_organizer_router

# third party import
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

# nest_asyncio.apply()

# Debug
# import debugpy
# debugpy.listen(("0.0.0.0", 5679))


# ********** Initialize FastAPI
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, title="CTSAPI v2")

# ********** Initialize CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Router
app.include_router(crm_document_organizer_router.router)

# Initialize security
security = HTTPBasic()

# Authentication credentials
SWAGGER_USERNAME = "master"
SWAGGER_PASSWORD = "secretsecret2025"


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, SWAGGER_USERNAME)
    is_password_correct = secrets.compare_digest(credentials.password, SWAGGER_PASSWORD)

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


# ********** OpenAPI


@app.get("/openapi.json")
async def get_open_api_endpoint(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    return JSONResponse(get_openapi(title="Citizen Debt Services API 2", version="1", routes=app.routes))


# ********** Docs


@app.get("/docs")
async def get_documentation(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="CTSAPI v2.1 Swagger",
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    )


# if __name__ == '__main__':
#     uvicorn.run("main:app", host="0.0.0.0", port=80, reload=True)
