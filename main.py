from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy", "message": "ultra minimal working"}

@app.get("/")
def root():
    return {"message": "Railway deployment test successful!"}