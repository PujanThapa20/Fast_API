from ortools.sat.python import cp_model
from typing import List
from models import Employee, ShiftType

class ShiftSchedulerConstraints:
    def __init__(self, model: cp_model.CpModel, employees: List[Employee], num_days: int = 7):
        self.model = model
        self.employees = employees
        self.num_days = num_days
        self.shift_types = [ShiftType.MORNING, ShiftType.EVENING, ShiftType.NIGHT]

    def apply_one_shift_per_day(self, shifts):
        """Constraint: An employee can work only one shift per day"""
        for employee in self.employees:
            for day in range(self.num_days):
                self.model.AddAtMostOne(shifts[(employee['id'], day, shift)] for shift in self.shift_types)

    def apply_max_weekly_shifts(self, shifts, max_shifts=5):
        """Constraint: Employee can work max X shifts per week (default 5)"""
        for employee in self.employees:
            total_shifts = []
            for day in range(self.num_days):
                for shift in self.shift_types:
                    total_shifts.append(shifts[(employee['id'], day, shift)])
            self.model.Add(sum(total_shifts) <= max_shifts)

    def apply_min_rest_time(self, shifts):
        """Constraint: Avoid back-to-back night and morning shifts"""
        for employee in self.employees:
            for day in range(self.num_days - 1):
                # If worked night shift, cannot work morning next day
                night_shift = shifts[(employee['id'], day, ShiftType.NIGHT)]
                next_morning = shifts[(employee['id'], day + 1, ShiftType.MORNING)]
                self.model.Add(night_shift + next_morning <= 1)

    def apply_no_consecutive_nights(self, shifts):
        """Constraint: No consecutive night shifts"""
        for employee in self.employees:
            for day in range(self.num_days - 1):
                night_shift = shifts[(employee['id'], day, ShiftType.NIGHT)]
                next_night = shifts[(employee['id'], day + 1, ShiftType.NIGHT)]
                self.model.Add(night_shift + next_night <= 1)

    def apply_exactly_5_work_days(self, shifts):
        """
        Constraint: Each employee must work exactly 5 days per week (2 full rest days)
        A 'work day' is any day with at least one shift assigned
        """
        for employee in self.employees:
            work_days = []
            for day in range(self.num_days):
                # Create a boolean variable indicating if employee worked this day
                worked = self.model.NewBoolVar(f"worked_{employee['id']}_{day}")
                # The employee worked if assigned to any shift this day
                self.model.AddMaxEquality(
                    worked,
                    [shifts[(employee['id'], day, shift)] for shift in self.shift_types]
                )
                work_days.append(worked)
            
            # Exactly 5 work days per week
            self.model.Add(sum(work_days) == 5)

    def apply_fair_distribution(self, shifts):
        """Soft constraint: Try to balance shifts evenly across employees"""
        # This will be implemented as an objective in the solver
        pass