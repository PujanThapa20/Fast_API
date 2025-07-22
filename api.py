from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import WorkCurbScheduler
import logging
import uvicorn
import os
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="WorkCurb Scheduler API", version="1.0.0")

# Configure CORS
origins = [
    "https://*.supabase.co",
    "https://*.railway.app",
    "http://localhost:*",
    "http://127.0.0.1:*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class ScheduleResponse(BaseModel):
    success: bool
    message: str
    timestamp: str
    schedule: Optional[dict] = None
    stats: Optional[dict] = None

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {str(e)}", exc_info=True)
        raise
    
    process_time = (datetime.now() - start_time).total_seconds()
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Response: {response.status_code} ({process_time:.2f}s)")
    
    return response

@app.post("/api/generate-schedule", response_model=ScheduleResponse)
async def generate_schedule():
    try:
        logger.info("Generating new schedule...")
        scheduler = WorkCurbScheduler()
        schedule = scheduler.generate_schedule()
        
        if not schedule or not schedule.get('assignments'):
            logger.warning("Schedule generation returned no assignments")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Schedule generation failed - no assignments created"
                }
            )
            
        logger.info(f"Generated schedule with {len(schedule['assignments'])} assignments")
        return {
            "success": True,
            "message": "Schedule generated successfully",
            "timestamp": datetime.now().isoformat(),
            "schedule": schedule.get('assignments'),
            "stats": schedule.get('stats')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating schedule: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Internal server error during schedule generation",
                "error": str(e)
            }
        )

@app.post("/api/delete-schedule", response_model=ScheduleResponse)
async def delete_schedule():
    try:
        logger.info("Deleting existing schedule...")
        scheduler = WorkCurbScheduler()
        success = scheduler.delete_schedule()
        
        if not success:
            logger.warning("Schedule deletion reported failure")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Schedule deletion failed"
                }
            )
            
        logger.info("Schedule deleted successfully")
        return {
            "success": True,
            "message": "Schedule deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting schedule: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Internal server error during schedule deletion",
                "error": str(e)
            }
        )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "WorkCurb Scheduler API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,
        workers=int(os.getenv("WEB_CONCURRENCY", 1)),
        timeout_keep_alive=int(os.getenv("UVICORN_TIMEOUT", 30)),
        access_log=True
    )