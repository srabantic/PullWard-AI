import os
from dotenv import load_dotenv
from google.adk import Agent
from google.genai import Client 

load_dotenv()

def init_pullward():
    print("Initializing PullWard AI Core Engine...")

    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables.")

    client = Client(api_key=api_key)

    # Instantiate base coordinator agent
    pullward_orchestrator = Agent(
        name="pullward_orchestrator",
        model="gemini-2.5-flash",
        instruction="You are PullWard AI, an autonomous PR governance, AST conflict analysis, and schema enforcement engine."
    )

    print(f"Agent '{pullward_orchestrator.name}' online and initialized successfully.")

if __name__ == "__main__":
    init_pullward()
    
