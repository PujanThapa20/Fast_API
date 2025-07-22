from supabase import create_client, Client
from typing import List, Optional
from models import Employee
import os
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized")

    def get_employees(self) -> List[Employee]:
        """Fetch all employees from the database"""
        try:
            response = self.client.table('employees').select("*").execute()
            logger.info(f"Fetched {len(response.data)} employees")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching employees: {str(e)}")
            return []

    def save_schedule(self, schedule: List[dict]) -> bool:
        """Save the generated schedule to the database"""
        try:
            # Delete old schedule first
            self.client.table('schedules').delete().neq('id', '').execute()
            
            # Insert new schedule in batches
            batch_size = 50
            for i in range(0, len(schedule), batch_size):
                batch = schedule[i:i + batch_size]
                self.client.table('schedules').insert(batch).execute()
            logger.info(f"Saved {len(schedule)} shifts to database")
            return True
        except Exception as e:
            logger.error(f"Error saving schedule: {str(e)}")
            return False

    def delete_schedule(self) -> bool:
        """Delete all schedule entries"""
        try:
            response = self.client.table('schedules').delete().neq('id', '').execute()
            logger.info(f"Deleted {len(response.data)} schedule entries")
            return True
        except Exception as e:
            logger.error(f"Error deleting schedule: {str(e)}")
            return False

    def get_current_schedule(self) -> List[dict]:
        """Get the current schedule from database"""
        try:
            response = self.client.table('schedules').select("*").execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching schedule: {str(e)}")
            return []