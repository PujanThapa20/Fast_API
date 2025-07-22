from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import WorkCurbScheduler
import logging
import uvicorn
import os
app = FastAPI()

# Configure CORS to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScheduleResponse(BaseModel):
    success: bool
    message: str
    schedule: Optional[dict]
    stats: Optional[dict]

@app.post("/api/generate-schedule", response_model=ScheduleResponse)
async def generate_schedule():
    try:
        scheduler = WorkCurbScheduler()
        schedule = scheduler.generate_schedule()
        if schedule:
            return {
                "success": True,
                "message": "Schedule generated successfully",
                "schedule": schedule.get('assignments'),
                "stats": schedule.get('stats')
            }
        raise HTTPException(status_code=400, detail="Schedule generation failed")
    except Exception as e:
        logging.error(f"Error generating schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/delete-schedule", response_model=ScheduleResponse)
async def delete_schedule():
    try:
        scheduler = WorkCurbScheduler()
        if scheduler.delete_schedule():
            return {
                "success": True,
                "message": "Schedule deleted successfully"
            }
        raise HTTPException(status_code=400, detail="Schedule deletion failed")
    except Exception as e:
        logging.error(f"Error deleting schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))