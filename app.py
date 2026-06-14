"""
Entry point for Hugging Face Spaces deployment.
This module starts the FastAPI server on the required HF Spaces port.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    import uvicorn
    from pm_rag.api.server import app
    
    # HF Spaces requires the app to run on port 7860
    port = int(os.getenv("PORT", 7860))
    host = "0.0.0.0"
    
    uvicorn.run(app, host=host, port=port)
