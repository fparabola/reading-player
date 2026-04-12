import urllib.request
import json

text = "Hello world. How are you?"

url = "http://localhost:8000/split"
data = json.dumps({"text": text, "language": "en"}).encode('utf-8')
req = urllib.request.Request(
    url,
    data=data,
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(result)
except urllib.error.HTTPError as e:
    print(f"Error: {e.code}")
    print(f"Response: {e.read().decode('utf-8')}")
