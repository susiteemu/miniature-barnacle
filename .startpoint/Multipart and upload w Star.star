url = "http://localhost:8000/multipart-form"
method = "POST"
headers = {
  "Content-Type": "multipart/form-data"
}
body = {
  "title": "Joku title tälle datalle",
  "file": "@resources/Python-logo.png",
}
