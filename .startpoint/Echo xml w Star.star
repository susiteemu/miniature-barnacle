url = "http://localhost:8000/echo"
method = "POST"
headers = {
  "Content-Type": "application/xml"
}
body = """
  <root>
    <id>1</id>
    <name>Jane</name>
  </root>
"""
