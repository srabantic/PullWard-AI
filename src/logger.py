import os
import uuid
from datetime import datetime, timezone
from google.cloud import bigquery
from typing import Dict, Any

def log_pr_audit_event(
    repo_name: str,
    pr_number: int,
    author: str,
    ast_conflicts_count: int,
    security_findings_count: int,
    schema_breaking_changes: bool,
    project_id: str = None
) -> Dict[str, Any]:
    """
    Streams a PullWard AI audit log entry directly into BigQuery.
    Falls back gracefully to local console logging if BigQuery is unavailable.
    """
    if not project_id:
        project_id = os.getenv("GCP_PROJECT_ID", "pullward-ai")
    project_id = str(project_id).strip()

    event_id = str(uuid.uuid4())
    row_to_insert = {
        "event_id": event_id,
        "repo_name": repo_name,
        "pr_number": pr_number,
        "author": author,
        "ast_conflicts_count": ast_conflicts_count,
        "security_findings_count": security_findings_count,
        "schema_breaking_changes": schema_breaking_changes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        client = bigquery.Client(project=project_id)
        dataset_id = f"{project_id}.pullward_audit"
        table_id = f"{dataset_id}.pr_audit_logs"

        errors = client.insert_rows_json(table_id, [row_to_insert])

        if not errors:
            print(f"Successfully streamed audit log for PR #{pr_number} in {repo_name} to BigQuery.")
            return {"status": "success", "event_id": event_id}
        else:
            print(f"Failed to stream audit log to BigQuery: {errors}")
            return {"status": "error", "details": errors, "event_id": event_id}

    except Exception as e:
        # Fallback to local console log if GCP/BigQuery authentication is missing
        print(f"[LOCAL AUDIT LOG] GCP BigQuery stream skipped ({e}). Event payload: {row_to_insert}")
        return {"status": "local_fallback", "event_id": event_id}


def fetch_recent_audit_logs(project_id: str = None, limit: int = 50) -> list:
    """
    Fetches the latest PR audit logs directly from BigQuery for permanent historical persistence.
    """
    if not project_id:
        project_id = os.getenv("GCP_PROJECT_ID", "pullward-ai")
    project_id = str(project_id).strip()

    try:
        client = bigquery.Client(project=project_id)
        query = f"""
            SELECT event_id, repo_name, pr_number, author, ast_conflicts_count, 
                   security_findings_count, schema_breaking_changes, timestamp
            FROM `{project_id}.pullward_audit.pr_audit_logs`
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        query_job = client.query(query)
        results = []
        for row in query_job:
            decision = "BLOCKED" if (row.schema_breaking_changes or (row.security_findings_count and row.security_findings_count > 0)) else ("NEEDS_REVIEW" if (row.ast_conflicts_count and row.ast_conflicts_count > 0) else "APPROVED")
            ts_str = row.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(row.timestamp, "strftime") else str(row.timestamp)
            results.append({
                "event_id": row.event_id,
                "repo_name": row.repo_name,
                "pr_number": row.pr_number,
                "pr_title": f"PR #{row.pr_number}",
                "author": row.author or "unknown",
                "html_url": f"https://github.com/{row.repo_name}/pull/{row.pr_number}",
                "ast_conflicts_count": row.ast_conflicts_count or 0,
                "security_findings_count": row.security_findings_count or 0,
                "schema_breaking_changes": bool(row.schema_breaking_changes),
                "decision": decision,
                "timestamp": ts_str,
                "details": {
                    "ast": {"findings": [f"AST signature conflict detected ({row.ast_conflicts_count})"] if row.ast_conflicts_count else []},
                    "security": {"findings": [f"Exposed secret / credential token detected ({row.security_findings_count})"] if row.security_findings_count else []},
                    "schema": {"findings": ["Destructive schema statement detected (DROP TABLE)"] if row.schema_breaking_changes else []}
                }
            })
        return results
    except Exception as e:
        print(f"[BIGQUERY FETCH] Querying BigQuery skipped ({e}). Using local in-memory fallback.")
        return []


if __name__ == "__main__":
    test_result = log_pr_audit_event(
        repo_name="Google-Patchamomma/PullWard-AI",
        pr_number=42,
        author="srabantichakraborty",
        ast_conflicts_count=1,
        security_findings_count=0,
        schema_breaking_changes=True
    )
    print("Test Log Streaming Output:", test_result)