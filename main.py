from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/health")
def health():
    port = os.environ.get("PORT", "unknown")
    return {
        "status": "healthy", 
        "message": "ultra minimal working",
        "port": port,
        "env_check": "ok"
    }

@app.get("/")
def root():
    return {"message": "Railway deployment test successful!", "port": os.environ.get("PORT", "unknown")}