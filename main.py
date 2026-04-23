from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from api.routes import router as api_router
import os

app = FastAPI(
    title="Cathedral Scanner",
    description="SRS engine for wallet data analysis",
    version="1.0.0"
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    # Return the landing page
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return {
            "message": "Cathedral Scanner API",
            "version": "1.0.0",
            "status": "operational"
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
