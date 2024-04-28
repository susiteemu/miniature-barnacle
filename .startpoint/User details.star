"""
meta:name: User details
meta:prev_req: Token
doc:url: http://localhost:8000/auth/oauth2/users/me/
doc:method: GET
"""
url = "http://localhost:8000/auth/oauth2/users/me/"
method = "GET"
auth = "Bearer " + prevResponse["body"]["access_token"]
headers = { "Authorization": auth }
