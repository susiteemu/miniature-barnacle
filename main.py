import logging
import random
import string
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

logger = logging.getLogger(__name__)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
#
# Authentication: oauth2
#
"""
SECRET_KEY = "13ada2c991825d6ee515f4fff8d98bbaabab2dc4c52f77329b13c29f3af31433"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/auth/oauth2/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/auth/oauth2/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


"""
#
# Authentication: basic auth
#
"""

basicAuthSecurity = HTTPBasic()


@app.get("/auth/basic/users/me")
def read_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(basicAuthSecurity)]
):
    return {"username": credentials.username, "password": credentials.password}


"""
#
# Random data endpoints
#
"""


def generate_random_string(length: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_xml() -> str:
    root = ET.Element("random_data")
    for _ in range(3):
        child = ET.SubElement(root, generate_random_string(5))
        child.text = generate_random_string(10)
    return ET.tostring(root, encoding="unicode", method="xml")


def generate_random_html() -> str:
    html_content = f"<html><body>{generate_random_string(50)}</body></html>"
    return html_content


@app.get("/random/json")
def random_json() -> Response:
    return JSONResponse(content={"data": generate_random_string(10)})


@app.get("/random/xml")
def random_xml() -> Response:
    return Response(
        content=generate_random_xml(),
        media_type="application/xml",
    )


@app.get("/random/plaintext")
def random_plaintext() -> Response:
    return Response(content=generate_random_string(50), media_type="text/plain")


@app.get("/random/html")
def random_html() -> HTMLResponse:
    return HTMLResponse(content=generate_random_html(), status_code=200)


"""
#
# Other endpoints
#
"""


@app.get("/status/{status}")
def status(status) -> Response:
    return Response(status_code=int(status))


@app.post("/echo")
async def echo(request: Request) -> Response:
    body = await request.body()
    return Response(headers=request.headers, content=body)


@app.post("/echo/{wait}")
async def echo(request: Request) -> Response:
    body = await request.body()
    wait = int(request.path_params["wait"])
    time.sleep(wait)
    return Response(headers=request.headers, content=body)


@app.post("/form")
async def form_data(request: Request) -> Response:
    form = await request.form()
    logger.info(f"Received form-data {form}")
    return JSONResponse(status_code=200, content={"form_data": form._dict})


@app.post("/multipart-form")
def multipart_form_data(
    title: str = Form(...), file: UploadFile = File(...)
) -> Response:
    return JSONResponse(
        status_code=200,
        content={
            "multipart_form_data": {
                "title": title,
                "file_name": file.filename,
                "file_size": len(file.file.read()),
            }
        },
    )


@app.post("/upload")
def upload_file(file: UploadFile) -> Response:
    return JSONResponse(
        content={"file_name": file.filename, "file_size": len(file.file.read())}
    )


@app.post("/download")
def download_file() -> Response:
    f = open("resources/Python-logo.png", mode="rb")
    data = f.read()
    f.close()
    return Response(content=data, media_type="application/octet-stream")
