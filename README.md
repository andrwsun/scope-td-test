# Scope TD Test Plugin

Minimal "Hello World" plugin to test TouchDesigner → Scope communication.

## What it does

1. Starts an HTTP server on port 5555
2. Receives messages from TouchDesigner
3. Displays them on screen
4. Prints to console when messages arrive

## Installation

```bash
cd scope-td-test
pip install -e .
```

## Testing

### 1. Test with curl (without TouchDesigner)

```bash
# Check if server is running
curl http://localhost:5555/ping

# Send a message
curl -X POST http://localhost:5555/message \
  -H 'Content-Type: application/json' \
  -d '{"message": "Hello from curl!"}'
```

### 2. Test from TouchDesigner

Create a **webDAT** in TouchDesigner with this Python code:

```python
import requests
import json

url = 'http://localhost:5555/message'
data = {'message': 'Hello from TouchDesigner!'}

response = requests.post(url, json=data)
print(response.json())
```

Or use the **Web DAT** operator:
- Method: POST
- URL: `http://localhost:5555/message`
- Request Header: `Content-Type: application/json`
- Request Data: `{"message": "Hello from TD!"}`

## Endpoints

- `POST /message` - Send a message to Scope
  - Body: `{"message": "your text here"}`
- `GET /ping` - Check if server is running
