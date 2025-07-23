from supabase import create_client
from typing import List
import os
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
        self.client = create_client(url, key)
        logger.info("Supabase client initialized")

    def get_employees(self) -> List[dict]:
        """Fetch all active employees from Supabase"""
        try:
            response = self.client.table('employees').select("*").execute()
            logger.info(f"Fetched {len(response.data)} employees from Supabase")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching employees: {str(e)}")
            return []