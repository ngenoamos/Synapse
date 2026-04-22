from fastapi import FastAPI
from api.routes import router as api_router

app = FastAPI(
    title="Cathedral Scanner",
    description="SRS engine for wallet data analysis",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Cathedral Scanner API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
