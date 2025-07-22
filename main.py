import os
from typing import Optional
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

from database import Database
from scheduler import ShiftScheduler
from models import Employee, ScheduleSolution

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorkCurbScheduler:
    def __init__(self):
        self.db = Database()
        self.current_schedule = None

    def fetch_employees(self) -> list[Employee]:
        """Fetch employees with validation"""
        employees = self.db.get_employees()
        if len(employees) < 3:
            logger.error(f"Need at least 3 employees, found {len(employees)}")
            return []
        return employees

    def generate_schedule(self) -> Optional[ScheduleSolution]:
        """Generate a new optimized schedule"""
        try:
            employees = self.fetch_employees()
            if not employees:
                return None

            # Generate new schedule
            scheduler = ShiftScheduler(employees)
            solution = scheduler.generate_schedule()

            if solution and solution.get('assignments'):
                if self.db.save_schedule(solution['assignments']):
                    self.current_schedule = solution
                    self.print_schedule(solution)
                    return solution
            return None
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return None

    def delete_schedule(self) -> bool:
        """Delete the current schedule"""
        if self.db.delete_schedule():
            self.current_schedule = None
            logger.info("Schedule deleted successfully")
            return True
        return False

    def print_schedule(self, solution: ScheduleSolution):
        """Print schedule summary"""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", 
               "Friday", "Saturday", "Sunday"]
        shifts = ["morning", "evening", "night"]

        print("\n=== CURRENT SCHEDULE ===")
        for day in range(7):
            print(f"\n{days[day]}:")
            for shift in shifts:
                assignment = next(
                    (a for a in solution['assignments'] 
                     if a['day'] == day and a['shift'] == shift),
                    None
                )
                print(f"  {shift:<7}: {assignment['employee_name'] if assignment else 'None'}")

if __name__ == "__main__":
    scheduler = WorkCurbScheduler()
    
    # Example usage:
    print("1. Generating schedule...")
    schedule = scheduler.generate_schedule()
    
    if schedule:
        print("\n2. Deleting schedule...")
        if scheduler.delete_schedule():
            print("\n3. Regenerating schedule...")
            new_schedule = scheduler.generate_schedule()