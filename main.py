import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from database import Database
from scheduler import ShiftScheduler

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def display_schedule(schedule):
    """Display the schedule in a readable format"""
    if not schedule or not schedule.get('assignments'):
        print("No schedule to display")
        return

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", 
           "Friday", "Saturday", "Sunday"]
    shifts = ["morning", "evening", "night"]
    
    print("\n" + "="*60)
    print("WEEKLY SHIFT SCHEDULE".center(60))
    print(f"Solution Seed: {schedule['stats']['random_seed']}".center(60))
    print("="*60)
    
    # Build schedule grid
    schedule_grid = {}
    for day in range(7):
        for shift in shifts:
            schedule_grid[(day, shift)] = "Unassigned"
    
    for assignment in schedule['assignments']:
        schedule_grid[(assignment['day'], assignment['shift'])] = assignment['employee_name']

    # Print schedule
    for day in range(7):
        print(f"\n{days[day]}:")
        for shift in shifts:
            print(f"  {shift.capitalize()}: {schedule_grid[(day, shift)]}")

    # Print statistics
    print("\n" + "="*60)
    print("SHIFT DISTRIBUTION".center(60))
    print("="*60)
    employee_counts = {}
    for assignment in schedule['assignments']:
        emp_id = assignment['employee_id']
        employee_counts[emp_id] = employee_counts.get(emp_id, 0) + 1
    
    for emp_id, count in employee_counts.items():
        emp_name = next(
            a['employee_name'] for a in schedule['assignments'] 
            if a['employee_id'] == emp_id
        )
        print(f"{emp_name}: {count} shifts")
    
    print("\n" + "="*60)
    print("STATISTICS".center(60))
    print("="*60)
    print(f"Total shifts assigned: {len(schedule['assignments'])}")
    print(f"Minimum shifts per employee: {schedule['stats']['min_shifts']}")
    print(f"Maximum shifts per employee: {schedule['stats']['max_shifts']}")
    print(f"Generated in {schedule['stats']['solve_time']:.2f} seconds")

def main():
    print("\nWORKCURB SHIFT SCHEDULER")
    print("="*60)
    
    # Initialize database connection
    db = Database()
    
    # Fetch employees from Supabase
    print("\nFetching employees...")
    employees = db.get_employees()
    if not employees:
        print("No employees found in database")
        return
    
    print(f"Found {len(employees)} employees")
    
    # Check minimum requirements
    min_employees = 5  # Minimum for feasible schedule
    if len(employees) < min_employees:
        print(f"\nWarning: Need at least {min_employees} employees for proper coverage")
    
    # Generate schedule
    print("\nGenerating optimized schedule...")
    scheduler = ShiftScheduler(employees)
    schedule = scheduler.generate_schedule()
    
    if schedule:
        display_schedule(schedule)
    else:
        print("\nFailed to generate schedule. Possible solutions:")
        print("- Add more employees")
        print("- Reduce number of required shifts")
        print("- Relax constraints in scheduler.py")

if __name__ == "__main__":
    main()
