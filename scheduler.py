from ortools.sat.python import cp_model
from typing import List, Dict, Tuple
from models import Employee, ShiftType, ShiftAssignment, ScheduleSolution
from constraints import ShiftSchedulerConstraints
import collections

class ShiftScheduler:
    def __init__(self, employees: List[Employee], num_days: int = 7):
        self.employees = employees
        self.num_days = num_days
        self.shift_types = [ShiftType.MORNING, ShiftType.EVENING, ShiftType.NIGHT]
        self.model = cp_model.CpModel()
        self.shifts = {}  # Dictionary to hold shift variables

    def create_shift_variables(self):
        """Create boolean variables for each possible shift assignment"""
        for employee in self.employees:
            for day in range(self.num_days):
                for shift in self.shift_types:
                    self.shifts[(employee['id'], day, shift)] = self.model.NewBoolVar(
                        f"shift_{employee['id']}_{day}_{shift}"
                    )

    def apply_constraints(self):
        """Apply all scheduling constraints"""
        constraints = ShiftSchedulerConstraints(self.model, self.employees, self.num_days)
        constraints.apply_one_shift_per_day(self.shifts)
        constraints.apply_max_weekly_shifts(self.shifts)
        constraints.apply_min_rest_time(self.shifts)
        constraints.apply_no_consecutive_nights(self.shifts)
        # Fair distribution is handled in the objective function

    def set_objectives(self):
        """Set optimization objectives for fair distribution"""
        # Objective 1: Maximize the number of assigned shifts
        total_shifts = []
        for key, var in self.shifts.items():
            total_shifts.append(var)
        self.model.Maximize(sum(total_shifts))

        # Objective 2: Minimize the difference in shifts assigned to employees
        # This helps in fair distribution
        employee_shifts = collections.defaultdict(list)
        for (emp_id, day, shift), var in self.shifts.items():
            employee_shifts[emp_id].append(var)
        
        # We'll minimize the maximum number of shifts assigned to any employee
        max_shifts = self.model.NewIntVar(0, self.num_days * len(self.shift_types), 'max_shifts')
        for emp_id, shifts in employee_shifts.items():
            self.model.AddMaxEquality(max_shifts, [sum(shifts)])
        self.model.Minimize(max_shifts)

    def solve(self) -> ScheduleSolution:
        """Solve the scheduling problem and return the solution"""
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            raise Exception("No solution found")

        assignments = []
        shift_counts = {emp['id']: 0 for emp in self.employees}

        # Collect all assignments
        for employee in self.employees:
            for day in range(self.num_days):
                for shift in self.shift_types:
                    if solver.Value(self.shifts[(employee['id'], day, shift)]) == 1:
                        assignments.append({
                            'employee_id': employee['id'],
                            'employee_name': employee['name'],
                            'day': day,
                            'shift': shift.value
                        })
                        shift_counts[employee['id']] += 1

        # Calculate statistics
        stats = {
            'total_shifts': len(assignments),
            'employee_stats': shift_counts,
            'solver_status': solver.StatusName(status),
            'solve_time': solver.WallTime()
        }

        return {
            'assignments': assignments,
            'stats': stats
        }

    def generate_schedule(self) -> ScheduleSolution:
        """Generate the complete schedule"""
        self.create_shift_variables()
        self.apply_constraints()
        self.set_objectives()
        return self.solve()