import os
import sys
from fastapi.testclient import TestClient

# Ensure src directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_webhook_ignored_event():
    response = client.post(
        "/webhook",
        headers={"x-github-event": "push"},
        json={"ref": "refs/heads/main"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert "push" in response.json()["reason"]


def test_webhook_ignored_pr_action():
    response = client.post(
        "/webhook",
        headers={"x-github-event": "pull_request"},
        json={
            "action": "closed",
            "pull_request": {"number": 1}
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert "closed" in response.json()["reason"]


def test_webhook_valid_pull_request():
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 10,
            "title": "Refactor user authentication service",
            "user": {"login": "octocat"},
            "diff_url": "",
            "comments_url": ""
        },
        "repository": {
            "full_name": "example/repo"
        }
    }
    response = client.post(
        "/webhook",
        headers={"x-github-event": "pull_request"},
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["repo"] == "example/repo"
    assert data["pr_number"] == 10
    assert data["decision"] in ["APPROVED", "NEEDS_REVIEW", "BLOCKED"]
