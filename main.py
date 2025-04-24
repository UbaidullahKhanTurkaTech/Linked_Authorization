from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import httpx
import os
from fastapi import status
from starlette.middleware.sessions import SessionMiddleware
from jose import jwt
import base64

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="testing_Linked13251632375226753284753264357")  # Use a strong secret!

app.mount("/static", StaticFiles(directory="static"), name="static")

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_PROFILE_URL = "https://api.linkedin.com/v2/me"


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    response = templates.TemplateResponse("home.html", {"request": request})
    response.delete_cookie("id_token")  # Forget previous login
    return response


@app.get("/login")
def login():
    # linkedin_url = (
        # f"{LINKEDIN_AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
        # f"&redirect_uri={REDIRECT_URI}&scope=r_liteprofile%20r_emailaddress"
    # )
    linkedin_url = (
    f"{LINKEDIN_AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}&scope=openid%20profile%20email"
    f"&prompt=login"
)
    return RedirectResponse(linkedin_url)

# @app.get("/callback")
# async def callback(request: Request, code: str):
    # token_data = {
        # "grant_type": "authorization_code",
        # "code": code,
        # "redirect_uri": REDIRECT_URI,
        # "client_id": CLIENT_ID,
        # "client_secret": CLIENT_SECRET
    # }

    # headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # try:
        # async with httpx.AsyncClient() as client:
            # # Exchange the code for an access token
            # token_resp = await client.post(LINKEDIN_TOKEN_URL, data=token_data, headers=headers)
            # token_json = token_resp.json()

            # access_token = token_json.get("access_token")
            # if not access_token:
                # return templates.TemplateResponse("error.html", {"request": request, "message": "Missing access_token"})

            # # Get the user's profile information using the access token
            # profile_resp = await client.get(
                # LINKEDIN_PROFILE_URL,
                # headers={"Authorization": f"Bearer {access_token}"}
            # )
            # profile_data = profile_resp.json()

            # # Return the profile data and set the access_token as a cookie
            # response = templates.TemplateResponse("success.html", {"request": request, "profile": profile_data})
            # response.set_cookie("access_token", access_token, httponly=True, max_age=3600)
            # return response

    # except Exception as e:
        # return templates.TemplateResponse("error.html", {"request": request, "message": str(e)})

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
                request.session["error_message"] = token_json.get("error_description", "Unknown error")
                return RedirectResponse("/error", status_code=status.HTTP_302_FOUND)

            id_token = token_json.get("id_token")
            if not id_token:
                request.session["error_message"] = "Missing id_token in response."
                return RedirectResponse("/error", status_code=status.HTTP_302_FOUND)

            decoded = jwt.decode(
                id_token,
                key="",  # Skipping signature verification
                options={"verify_signature": False},
                audience=CLIENT_ID
            )

            request.session["user_profile"] = decoded
            # return RedirectResponse("/success", status_code=status.HTTP_302_FOUND)
            response = RedirectResponse(url="/success", status_code=status.HTTP_302_FOUND)
            response.set_cookie("id_token", id_token, httponly=True, max_age=3600)
            return response

    except Exception as e:
        request.session["error_message"] = str(e)
        return RedirectResponse("/error", status_code=status.HTTP_302_FOUND)
        
@app.get("/success")
def success_page(request: Request):
    user = request.session.get("user_profile", {})
    return templates.TemplateResponse("success.html", {"request": request, "profile": user})

@app.get("/error")
def error_page(request: Request):
    error_msg = request.session.get("error_message", "Unknown error")
    return templates.TemplateResponse("error.html", {"request": request, "message": error_msg})
    
@app.get("/policy", response_class=HTMLResponse)
def policy(request: Request):
    return templates.TemplateResponse("policy.html", {"request": request})

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("id_token")
    return response