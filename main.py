from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from api.routes import router as api_router

app = FastAPI(
    title="Cathedral Scanner",
    description="SRS engine for wallet data analysis",
    version="1.0.0"
)

# Configure CORS - This fixes your error!
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ngenoamos.github.io",  # Your GitHub Pages
        "http://localhost:8080",         # Local development
        "http://localhost:8000",         # Local API
        "https://*.railway.app",         # Railway domains
    ],
    allow_credentials=True,
    allow_methods=["*"],                 # Allow all HTTP methods
    allow_headers=["*"],                 # Allow all headers
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
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
