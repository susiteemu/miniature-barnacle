import logging
import random
import string
import xml.etree.ElementTree as ET

from fastapi import FastAPI, File, Form, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/status/{status}")
def status(status) -> Response:
    return Response(status_code=int(status))


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


@app.post("/echo")
async def echo(request: Request) -> Response:
    body = await request.body()
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
