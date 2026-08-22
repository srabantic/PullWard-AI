#!/usr/bin/env python3
"""
PullWard AI - Local Webhook End-to-End Simulation Script
Sends simulated GitHub Pull Request payloads to the local FastAPI server.
"""

import sys
import httpx
import json

LOCAL_WEBHOOK_URL = "http://localhost:8080/webhook"

# Simulated PR diff containing:
# 1. AST breaking change (function removed)
# 2. Security issue (hardcoded API key)
# 3. Schema breaking change (DROP TABLE)
MOCK_PR_PAYLOAD = {
    "action": "opened",
    "pull_request": {
        "number": 42,
        "title": "Feature: Refactor database schema and authentication service",
        "user": {"login": "dev-user"},
        "diff_url": "",
        "comments_url": ""
    },
    "repository": {
        "full_name": "demo-org/sample-repo"
    }
}


def test_local_server():
    print(f"📡 Sending simulated GitHub PR payload to {LOCAL_WEBHOOK_URL}...")

    try:
        response = httpx.post(
            LOCAL_WEBHOOK_URL,
            headers={
                "X-GitHub-Event": "pull_request",
                "Content-Type": "application/json"
            },
            json=MOCK_PR_PAYLOAD,
            timeout=10.0
        )

        print(f"Status Code: {response.status_code}")
        print("Response Payload:")
        print(json.dumps(response.json(), indent=2))

    except httpx.ConnectError:
        print("❌ Could not connect to local server. Make sure 'python main.py' is running in another terminal!")
        sys.exit(1)


if __name__ == "__main__":
    test_local_server()
