from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from api.routes import router as api_router
from pathlib import Path

app = FastAPI(
    title="Cathedral Scanner",
    description="SRS engine for wallet data analysis",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ngenoamos.github.io",
        "http://localhost:8080",
        "http://localhost:8000",
        "https://*.railway.app",
        "https://*.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Get the directory where this script is located
BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend-tailwind" / "src"

@app.get("/")
async def root():
    """Serve your Tailwind UI at root"""
    index_path = FRONTEND_DIR / "index.html"
    try:
        with open(index_path, "r") as f:
            content = f.read()
            # Fix CSS path
            content = content.replace('./output.css', '/output.css')
            return HTMLResponse(content=content)
    except FileNotFoundError:
        return {
            "message": "Cathedral Scanner API",
            "version": "1.0.0",
            "status": "operational",
            "frontend_path": str(FRONTEND_DIR)
        }

@app.get("/output.css")
async def serve_css():
    """Serve the Tailwind CSS file"""
    css_path = FRONTEND_DIR / "output.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return {"error": "CSS file not found"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}