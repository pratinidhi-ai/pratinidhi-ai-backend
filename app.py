"""
Main FastAPI Application Entry Point
"""

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout for AWS App Runner
    ],
    force=True  # Override any existing logging configuration
)
logger = logging.getLogger(__name__)
logger.info(f"Application starting with log level: {log_level}")

# Create FastAPI app
app = FastAPI(
    title="Pratinidhi AI Backend",
    description="Backend API for Pratinidhi AI application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
try:
    from routes.user_routing import user_router
    from routes.tutor_routing import tutor_router
    from routes.task_routing import task_router
    from routes.question_routing import question_router
    from routes.analytics_routing import analytics_router
    from routes.math_tutor_routing import math_tutor_router
    from routes.leaderboard_routing import router as leaderboard_router

    app.include_router(user_router)
    app.include_router(tutor_router)
    app.include_router(task_router, prefix='/api/tasks')
    app.include_router(question_router, prefix='/api/questions')
    app.include_router(analytics_router, prefix='/api/analytics')
    app.include_router(math_tutor_router, prefix='/api/math_tutor')
    app.include_router(leaderboard_router)
    logger.info("Routers loaded successfully")
except Exception as e:
    logger.error(f"Failed to load routers: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Pratinidhi AI Backend API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}

@app.get('/check-user-exists')
async def check_user_exists(uid: str = Query(None, description="User ID to check")):
    logger.info(f"Checking user existence for uid: {uid}")
    if uid is None:
        logger.warning("check-user-exists called without uid parameter")
        raise HTTPException(status_code=400, detail='uid parameter is required')
    from database.user_db import checkUserExists
    exists = checkUserExists(user_id=uid)
    logger.info(f"User {uid} exists: {exists}")
    return {'exists': exists}

@app.get('/users')
async def users():
    logger.info("Fetching all users")
    from database.user_db import getUsers
    user_list = getUsers()
    logger.info(f"Retrieved {len(user_list)} users")
    return user_list

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    logger.warning(f"404 Not Found: {request.url.path}")
    return JSONResponse(
        status_code=404,
        content={'error': 'Not found', 'message': 'The requested resource was not found'}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"500 Internal Server Error: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={'error': 'Internal server error', 'message': 'Something went wrong'}
    )

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Pratinidhi AI Backend...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Pratinidhi AI Backend...")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://0.0.0.0:8000")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)