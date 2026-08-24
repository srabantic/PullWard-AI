import os
import sys
import re
import hmac
import hashlib
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException

load_dotenv()

# Ensure the parent directory and current directory are on the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents import run_pullward_governance_orchestrator
from logger import log_pr_audit_event

app = FastAPI(title="PullWard AI - PR Governance Webhook")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")


def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verifies that the incoming webhook payload came from GitHub."""
    if not GITHUB_WEBHOOK_SECRET or not signature_header:
        return True  # Skip check if secret is not configured in env

    try:
        sha_name, signature = signature_header.split("=")
        if sha_name != "sha256":
            return False
        mac = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), msg=payload_body, digestmod=hashlib.sha256)
        return hmac.compare_digest(mac.hexdigest(), signature)
    except Exception:
        return False


def parse_diff_files(diff_text: str):
    """Splits a unified diff into individual file chunks and extracts old vs new code lines."""
    file_diffs = []
    chunks = re.split(r'^diff --git a/(.*?) b/(.*?)$', diff_text, flags=re.MULTILINE)

    for i in range(1, len(chunks), 3):
        new_name = chunks[i + 1]
        body = chunks[i + 2]

        old_lines = []
        new_lines = []

        for line in body.splitlines():
            if line.startswith('-') and not line.startswith('---'):
                old_lines.append(line[1:])
            elif line.startswith('+') and not line.startswith('+++'):
                new_lines.append(line[1:])
            elif not line.startswith(('@@', '---', '+++', 'index ')):
                old_lines.append(line)
                new_lines.append(line)

        file_diffs.append({
            "filename": new_name,
            "old_code": "\n".join(old_lines),
            "new_code": "\n".join(new_lines)
        })

    return file_diffs


@app.get("/")
def read_root():
    return {"status": "healthy", "service": "PullWard AI Governance Gatekeeper"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None)
):
    body_bytes = await request.body()

    # 1. Webhook Signature Security Validation
    if not verify_github_signature(body_bytes, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature")

    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": f"Event '{x_github_event}' is not a pull_request"}

    payload = await request.json()
    action = payload.get("action")

    if action not in ["opened", "synchronize", "reopened"]:
        return {"status": "ignored", "reason": f"Action '{action}' does not require analysis"}

    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})

    repo_name = repo_data.get("full_name", "unknown/repo")
    pr_number = pr_data.get("number", 0)
    pr_title = pr_data.get("title", "")
    author = pr_data.get("user", {}).get("login", "unknown")
    diff_url = pr_data.get("diff_url", "")
    comments_url = pr_data.get("comments_url", "")

    # 2. Fetch raw PR diff from GitHub
    diff_text = ""
    if diff_url and diff_url.startswith(("http://", "https://")):
        async with httpx.AsyncClient() as client:
            headers = {"User-Agent": "PullWard-AI-Bot"}
            if GITHUB_TOKEN:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"

            diff_response = await client.get(diff_url, headers=headers)
            if diff_response.status_code == 200:
                diff_text = diff_response.text

    # 3. Parse diff into file chunks
    parsed_files = parse_diff_files(diff_text)

    # 4. Execute Multi-Agent Governance Orchestration (AST, Security, Schema Agents)
    gov_result = run_pullward_governance_orchestrator(pr_title, diff_text, parsed_files)

    # 5. Stream Audit Log to BigQuery
    log_res = log_pr_audit_event(
        repo_name=repo_name,
        pr_number=pr_number,
        author=author,
        ast_conflicts_count=gov_result["ast_conflicts_count"],
        security_findings_count=gov_result["security_findings_count"],
        schema_breaking_changes=gov_result["schema_breaking_changes"]
    )

    # 6. Post Consolidated Governance Report back to GitHub PR
    github_token = os.getenv("GITHUB_TOKEN", "")
    if not comments_url and pr_data.get("issue_url"):
        comments_url = pr_data.get("issue_url") + "/comments"

    if github_token and comments_url:
        comment_body = gov_result["comment_markdown"] + f"\n\n*Audit Log Event ID:* `{log_res.get('event_id', 'N/A')}`"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                comments_url,
                json={"body": comment_body},
                headers={
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            print(f"Posted comment to GitHub PR: {comments_url} -> Status {resp.status_code}")
    else:
        print(f"Skipped posting GitHub comment. Token present: {bool(github_token)}, URL present: {bool(comments_url)}")

    return {
        "status": "processed",
        "repo": repo_name,
        "pr_number": pr_number,
        "decision": gov_result["decision"],
        "audit_event_id": log_res.get("event_id")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=True)