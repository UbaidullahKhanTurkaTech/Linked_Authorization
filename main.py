from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import httpx
import os

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_PROFILE_URL = "https://api.linkedin.com/v2/me"


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/login")
def login():
    # linkedin_url = (
        # f"{LINKEDIN_AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
        # f"&redirect_uri={REDIRECT_URI}&scope=r_liteprofile%20r_emailaddress"
    # )
    linkedin_url = (
    f"{LINKEDIN_AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}&scope=openid%20profile%20email"
)

    return RedirectResponse(linkedin_url)

from jose import jwt
import base64

@app.get("/callback")
async def callback(request: Request, code: str):
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(LINKEDIN_TOKEN_URL, data=token_data, headers=headers)
            token_json = token_resp.json()

            if "error" in token_json:
                return templates.TemplateResponse("error.html", {"request": request, "message": token_json.get("error_description", "Unknown error")})

            id_token = token_json.get("id_token")
            if not id_token:
                return templates.TemplateResponse("error.html", {"request": request, "message": "Missing id_token in response."})

            # Decode without signature verification (since LinkedIn doesn't expose JWKS for OIDC)
            decoded = jwt.decode(
                                id_token,
                                key="",  # Signature verification skipped
                                options={"verify_signature": False},
                                audience=CLIENT_ID  # Required to match LinkedIn's 'aud'
                            )
            return templates.TemplateResponse("success.html", {"request": request, "profile": decoded})

    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "message": str(e)})
# @app.get("/callback")
# async def callback(request: Request, code: str = None, error: str = None):
    # if error:
        # return templates.TemplateResponse("error.html", {"request": request, "error": error})

    # try:
        # async with httpx.AsyncClient() as client:
            # token_resp = await client.post(
                # LINKEDIN_TOKEN_URL,
                # data={
                    # "grant_type": "authorization_code",
                    # "code": code,
                    # "redirect_uri": REDIRECT_URI,
                    # "client_id": CLIENT_ID,
                    # "client_secret": CLIENT_SECRET,
                # },
                # headers={"Content-Type": "application/x-www-form-urlencoded"},
            # )

            # token_resp.raise_for_status()
            # access_token = token_resp.json().get("access_token")

            # profile_resp = await client.get(
                # LINKEDIN_PROFILE_URL,
                # headers={"Authorization": f"Bearer {access_token}"},
            # )

            # profile_resp.raise_for_status()
            # profile_data = profile_resp.json()
            # return templates.TemplateResponse("success.html", {"request": request, "profile": profile_data})
    # except Exception as e:
        # return templates.TemplateResponse("error.html", {"request": request, "error": str(e)})


@app.get("/policy", response_class=HTMLResponse)
def policy(request: Request):
    return templates.TemplateResponse("policy.html", {"request": request})
