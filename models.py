from typing import List, TypedDict
from enum import Enum

class ShiftType(Enum):
    MORNING = "morning"
    EVENING = "evening"
    NIGHT = "night"

class Employee(TypedDict):
    id: str
    name: str
    max_shifts_per_week: int

class ShiftAssignment(TypedDict):
    employee_id: str
    employee_name: str
    day: int  # 0-6 for Monday-Sunday
    shift: ShiftType

class ScheduleSolution(TypedDict):
    assignments: List[ShiftAssignment]
    stats: dict