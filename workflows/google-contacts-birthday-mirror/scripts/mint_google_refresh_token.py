#!/usr/bin/env python3

import http.server
import json
import secrets
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path


CLIENT_SECRET_PATH = Path(__file__).resolve().parents[1] / "client_secret_551884711893-l8n5l52ki23ceitgasrju0bgb6igks50.apps.googleusercontent.com.json"
REDIRECT_URI = "http://localhost:8765/"
SCOPES = [
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/calendar",
]


def main() -> int:
    client = json.loads(CLIENT_SECRET_PATH.read_text())["installed"]
    state = secrets.token_urlsafe(24)
    result = {"code": None, "error": None, "state": None}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            result["code"] = qs.get("code", [None])[0]
            result["error"] = qs.get("error", [None])[0]
            result["state"] = qs.get("state", [None])[0]
            body = "Authorization received. You can close this tab." if result["code"] else "Authorization failed. You can close this tab."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, fmt, *args):
            return

    server = http.server.HTTPServer(("127.0.0.1", 8765), Handler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    params = {
        "client_id": client["client_id"],
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    print("Open this URL and complete consent:\n")
    print(auth_url)
    print("\nWaiting for Google to redirect back to localhost...\n")

    for _ in range(600):
        if result["code"] or result["error"]:
            break
        time.sleep(1)

    server.server_close()

    if result["error"]:
        raise SystemExit(f"OAuth error: {result['error']}")
    if result["state"] != state:
        raise SystemExit("OAuth state mismatch")
    if not result["code"]:
        raise SystemExit("Timed out waiting for OAuth callback")

    body = urllib.parse.urlencode(
        {
            "code": result["code"],
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    ).encode()
    request = urllib.request.Request("https://oauth2.googleapis.com/token", data=body, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        token_data = json.loads(response.read().decode())

    print(json.dumps(token_data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
