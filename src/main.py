import os
import sys
import re
import hmac
import hashlib
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

# Ensure the parent directory and current directory are on the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents import run_pullward_governance_orchestrator
from logger import log_pr_audit_event, fetch_recent_audit_logs

app = FastAPI(title="PullWard AI - PR Governance Webhook")

# Mount assets directory to serve logo.png (e.g., /assets/logo.png)
assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
if not os.path.exists(assets_path):
    assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# Initialize Jinja2 templates directory
templates_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=templates_path)

# Live audit logs store for real-time dashboard visualization
in_memory_audit_logs = []

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
    if not diff_text:
        return []

    file_diffs = []
    chunks = re.split(r'^diff --git a/(.*?) b/(.*?)$', diff_text, flags=re.MULTILINE)

    if len(chunks) >= 3:
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
    else:
        # Fallback for single file patch or raw snippet
        old_lines = []
        new_lines = []
        for line in diff_text.splitlines():
            if line.startswith('-') and not line.startswith('---'):
                old_lines.append(line[1:])
            elif line.startswith('+') and not line.startswith('+++'):
                new_lines.append(line[1:])
            elif not line.startswith(('@@', '---', '+++', 'index ')):
                old_lines.append(line)
                new_lines.append(line)
        file_diffs.append({
            "filename": "patch.sql",
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


def get_current_audit_logs():
    """Returns in-memory logs, hydrating from BigQuery if empty."""
    global in_memory_audit_logs
    if not in_memory_audit_logs:
        bq_records = fetch_recent_audit_logs(limit=50)
        if bq_records:
            in_memory_audit_logs.extend(bq_records)
    return in_memory_audit_logs


@app.get("/api/logs")
async def get_live_audit_logs():
    """Returns real-time JSON data for the dashboard auto-polling stream."""
    logs = get_current_audit_logs()
    stats = {
        "total_prs": len(logs),
        "breaking_changes": sum(1 for log in logs if log.get("schema_breaking_changes") or log.get("ast_conflicts_count", 0) > 0),
        "blocked_prs": sum(1 for log in logs if log.get("decision") == "BLOCKED" or log.get("schema_breaking_changes") or log.get("security_findings_count", 0) > 0),
        "latest_event_id": logs[0]["event_id"] if logs else "None"
    }
    
    ast_conflicts_total = sum(log.get("ast_conflicts_count", 0) for log in logs)
    security_secrets_total = sum(log.get("security_findings_count", 0) for log in logs)
    schema_drops_total = sum(1 for log in logs if log.get("schema_breaking_changes"))

    chart_data = {
        "ast_bar": [ast_conflicts_total, 0, 0],
        "security_donut": [security_secrets_total, 0, schema_drops_total]
    }
    
    return {
        "stats": stats,
        "logs": logs,
        "chart_data": chart_data
    }


@app.get("/dashboard")
async def render_dashboard(request: Request):
    """Renders the real-time PR Governance Monitor UI powered by live PR events and BigQuery history."""
    logs = get_current_audit_logs()
    stats = {
        "total_prs": len(logs),
        "breaking_changes": sum(1 for log in logs if log.get("schema_breaking_changes") or log.get("ast_conflicts_count", 0) > 0),
        "blocked_prs": sum(1 for log in logs if log.get("decision") == "BLOCKED" or log.get("schema_breaking_changes") or log.get("security_findings_count", 0) > 0),
        "latest_event_id": logs[0]["event_id"] if logs else "None"
    }
    
    ast_conflicts_total = sum(log.get("ast_conflicts_count", 0) for log in logs)
    security_secrets_total = sum(log.get("security_findings_count", 0) for log in logs)
    schema_drops_total = sum(1 for log in logs if log.get("schema_breaking_changes"))

    chart_data = {
        "ast_bar": [ast_conflicts_total, 0, 0],
        "security_donut": [security_secrets_total, 0, schema_drops_total]
    }
    
    context = {
        "request": request,
        "logs": logs,
        "stats": stats,
        "chart_data": chart_data
    }
    
    return templates.TemplateResponse(request, "dashboard.html", context)


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

    # 2. Fetch raw PR diff directly from GitHub REST API
    diff_text = ""
    github_token = os.getenv("GITHUB_TOKEN", "")
    api_pr_url = pr_data.get("url")
    if api_pr_url:
        async with httpx.AsyncClient() as client:
            headers = {
                "User-Agent": "PullWard-AI-Bot",
                "Accept": "application/vnd.github.v3.diff"
            }
            if github_token:
                headers["Authorization"] = f"token {github_token}"
            diff_response = await client.get(api_pr_url, headers=headers)
            if diff_response.status_code == 200:
                diff_text = diff_response.text
    print(f"Fetched PR #{pr_number} diff: {len(diff_text)} bytes.")

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

    # Record log entry in-memory for the live UI dashboard stream
    import datetime
    audit_entry = {
        "event_id": log_res.get("event_id", "N/A"),
        "repo_name": repo_name,
        "pr_number": pr_number,
        "pr_title": pr_title or f"PR #{pr_number}",
        "author": author,
        "html_url": pr_data.get("html_url", f"https://github.com/{repo_name}/pull/{pr_number}"),
        "ast_conflicts_count": gov_result["ast_conflicts_count"],
        "security_findings_count": gov_result["security_findings_count"],
        "schema_breaking_changes": gov_result["schema_breaking_changes"],
        "decision": gov_result["decision"],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC"),
        "comment_markdown": gov_result.get("comment_markdown", ""),
        "details": gov_result.get("details", {})
    }
    in_memory_audit_logs.insert(0, audit_entry)

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
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)