import os
import sys
from dotenv import load_dotenv

# Ensure root and src directories are in Python path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "src"))

load_dotenv()

from src.main import app

def run_server():
    """Launches the PullWard AI FastAPI Governance Gateway server."""
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting PullWard AI Core Governance Gateway on {host}:{port}...")
    uvicorn.run("src.main:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    run_server()

