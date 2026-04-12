# Compatibility shim for OpenEnv validator
from backend.main import app as backend_app
import uvicorn

def main():
    """Main entry point for the server shim."""
    print("🚀 Starting OpenEnv Customer Support (Shim)...")
    uvicorn.run(backend_app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
