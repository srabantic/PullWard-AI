# 🛡️ PullWard AI - Autonomous PR Governance & AST Safety Engine

PullWard AI is an autonomous multi-agent code governance, AST conflict analysis, security vulnerability scanning, and schema breaking change enforcement engine built with **Google ADK (Agent Development Kit)**, **Google Gemini (`gemini-2.5-flash`)**, **FastAPI**, and **Google Cloud BigQuery**.

---

## 📐 Architecture Overview

PullWard AI leverages **Google ADK (`google.adk.Agent`)** to define specialized domain agents and supervisor orchestrators.

```
                        ┌───────────────────────────────┐
                        │    GitHub PR Webhook Event    │
                        └──────────────┬────────────────┘
                                       │
                                       ▼
                        ┌───────────────────────────────┐
                        │   FastAPI Governance Gateway  │
                        │        (src/main.py)          │
                        └──────────────┬────────────────┘
                                       │
                                       ▼
                        ┌───────────────────────────────┐
                        │ Google ADK Supervisor Agent   │
                        │    (agents/orchestrator.py)   │
                        └───────┬───────┬───────┬───────┘
                                │       │       │
       ┌───────────────────────┘       │       └────────────────────────┐
       ▼                               ▼                                ▼
┌─────────────────────────┐  ┌───────────────────┐  ┌─────────────────────────────┐
│  AST Governance Agent   │  │  Security Agent   │  │    Schema Safety Agent      │
│  - Python AST Visitor   │  │  - Secret Scanner │  │  - Destructive SQL drops    │
│  - Signature Fallbacks  │  │  - Dangerous eval │  │  - Schema breaking changes  │
└────────────┬────────────┘  └─────────┬─────────┘  └──────────────┬──────────────┘
             │                         │                           │
             └─────────────────────────┼───────────────────────────┘
                                       │
                                       ▼
                   ┌────────────────────────────────────────┐
                   │ Consolidated Verdict:                  │
                   │ APPROVED / NEEDS_REVIEW / BLOCKED      │
                   └───────────────────┬────────────────────┘
                                       │
               ┌───────────────────────┴───────────────────────┐
               ▼                                               ▼
┌─────────────────────────────┐                 ┌─────────────────────────────┐
│ Stream Audit Event to GCP   │                 │ Post Governance Report to   │
│ BigQuery (logger.py)        │                 │ GitHub PR Comments          │
└─────────────────────────────┘                 └─────────────────────────────┘
```

---

## 🤖 Specialized Multi-Agent Division (Google ADK Framework)

1. **PullWard Orchestrator** ([`src/agents/orchestrator.py`](file:///Users/srabantichakraborty/Desktop/Google%20Cloud%20Patchamomma%202026/PullWard-AI/src/agents/orchestrator.py)): Built with **Google ADK (`google.adk.Agent`)**. Coordinates specialized sub-agents, aggregates domain evaluations, and determines final pull request verdict (`APPROVED`, `NEEDS_REVIEW`, `BLOCKED`).
2. **AST Governance Agent** ([`src/agents/ast_agent.py`](file:///Users/srabantichakraborty/Desktop/Google%20Cloud%20Patchamomma%202026/PullWard-AI/src/agents/ast_agent.py)): Performs deterministic AST parsing across Python, TypeScript, JavaScript, C#, Java, and Go to flag removed functions, modified parameter signatures, or deleted class definitions.
3. **Security Sub-Agent** ([`src/agents/security_agent.py`](file:///Users/srabantichakraborty/Desktop/Google%20Cloud%20Patchamomma%202026/PullWard-AI/src/agents/security_agent.py)): Scans code diffs for exposed secrets (Google API keys, GitHub tokens, RSA private keys) and dangerous execution functions (`eval()`, `exec()`, raw SQL concatenation).
4. **Schema Safety Agent** ([`src/agents/schema_agent.py`](file:///Users/srabantichakraborty/Desktop/Google%20Cloud%20Patchamomma%202026/PullWard-AI/src/agents/schema_agent.py)): Detects high-risk destructive database statements (`DROP TABLE`, `DROP COLUMN`, `DROP DATABASE`).

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and configure your API credentials:

```bash
cp .env.example .env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini API key from AI Studio or Vertex AI | Required |
| `GEMINI_MODEL` | Gemini model version | `gemini-2.5-flash` |
| `GCP_PROJECT_ID` | Google Cloud Platform project ID for BigQuery | `pullward-ai` |
| `BIGQUERY_DATASET` | BigQuery audit logs dataset name | `pullward_audit` |
| `GITHUB_WEBHOOK_SECRET` | Secret key used to verify HMAC SHA-256 signatures | Optional |
| `GITHUB_TOKEN` | Personal Access Token to post comments back to PR | Optional |
| `PORT` | Webhook HTTP port | `8080` |

---

## 🚀 Quickstart & Local Development

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch Local Server
```bash
python main.py
```
The server will start at `http://localhost:8080`.

### 3. Run Test Suite
```bash
pytest tests/ -v
```

---

## 📦 Containerization & Deployment

### Run with Docker locally
```bash
docker build -t pullward-ai .
docker run -p 8080:8080 --env-file .env pullward-ai
```

### Deploy to Google Cloud Run
Make sure you are authenticated with `gcloud`, then run:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📊 BigQuery Audit Setup

To initialize the BigQuery dataset (`pullward_audit`) and audit table (`pr_audit_logs`), run:
```bash
python src/schemas.py
```
