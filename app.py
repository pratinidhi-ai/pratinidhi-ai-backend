from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

from database.user_db import getUsers, checkUserExists, getUserbyId
from helper.middleware import authenticate_request
from routes.user_routing import user_router
from routes.tutor_routing import tutor_router
from routes.task_routing import task_router
from routes.question_routing import question_router
from routes.analytics_routing import analytics_router
from routes.math_tutor_routing import math_tutor_router
from routes.leaderboard_routing import leaderboard_router

# Configure logging for the entire application
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
	level=getattr(logging, log_level, logging.INFO),
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	handlers=[
		logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout for AWS App Runner
	],
	force=True  # Override any existing logging configuration
)

# Create logger for this module
logger = logging.getLogger(__name__)
logger.info(f"Application starting with log level: {log_level}")

app = FastAPI(title="User API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

logger.info("FastAPI app initialized")

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

# Include routers
app.include_router(user_router)
app.include_router(tutor_router)
app.include_router(task_router, prefix='/api/tasks')
app.include_router(question_router, prefix='/api/questions')
app.include_router(analytics_router, prefix='/api/analytics')
app.include_router(math_tutor_router, prefix='/api/math_tutor')
app.include_router(leaderboard_router)


# Health check endpoint
@app.get('/')
async def health_check():
	logger.info("Health check endpoint called")
	return {'status': 'healthy', 'service': 'user-api'}


@app.get('/check-user-exists')
async def check_user_exists(uid: str = Query(None, description="User ID to check")):
	logger.info(f"Checking user existence for uid: {uid}")
	if uid is None:
		logger.warning("check-user-exists called without uid parameter")
		raise HTTPException(status_code=400, detail='uid parameter is required')
	exists = checkUserExists(user_id=uid)
	logger.info(f"User {uid} exists: {exists}")
	return {'exists': exists}


@app.get('/users')
async def users():
	logger.info("Fetching all users")
	user_list = getUsers()
	logger.info(f"Retrieved {len(user_list)} users")
	return user_list

if __name__ == "__main__":
	import uvicorn
	logger.info("Starting FastAPI application on 0.0.0.0:8080")
	uvicorn.run(app, host='0.0.0.0', port=8080)