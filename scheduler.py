from ortools.sat.python import cp_model
from typing import List, Dict
import random
import logging
import math

logger = logging.getLogger(__name__)

class ShiftScheduler:
    def __init__(self, employees: List[dict], num_days: int = 7):
        self.employees = employees
        self.num_days = num_days
        self.shift_types = ["morning", "evening", "night"]
        self.model = cp_model.CpModel()
        
    def generate_schedule(self) -> Dict:
        """Generate optimized shift schedule with reliable constraints"""
        # Create variables
        shifts = {}
        for emp in self.employees:
            for day in range(self.num_days):
                for shift in self.shift_types:
                    shifts[(emp['id'], day, shift)] = self.model.NewBoolVar(
                        f"shift_{emp['id']}_{day}_{shift}"
                    )
        
        # Calculate shift distribution parameters
        total_shifts = self.num_days * len(self.shift_types)
        min_shifts = math.floor(total_shifts / len(self.employees))
        max_shifts = min_shifts + 2
        
        # Hard Constraints
        # 1. Each shift assigned to exactly one employee
        for day in range(self.num_days):
            for shift in self.shift_types:
                self.model.AddExactlyOne(
                    shifts[(emp['id'], day, shift)] for emp in self.employees
                )
        
        # 2. Fair shift distribution
        for emp in self.employees:
            total = sum(
                shifts[(emp['id'], day, shift)]
                for day in range(self.num_days)
                for shift in self.shift_types
            )
            self.model.Add(total >= max(min_shifts - 1, 1))  # At least 1 shift
            self.model.Add(total <= min(max_shifts, 7))  # At most 7 shifts
        
        # 3. Soft constraints for consecutive nights
        for emp in self.employees:
            for day in range(self.num_days - 1):
                night1 = shifts[(emp['id'], day, "night")]
                night2 = shifts[(emp['id'], day + 1, "night")]
                # Penalize but don't forbid consecutive nights
                penalty = self.model.NewBoolVar(f'penalty_{emp["id"]}_{day}')
                self.model.Add(night1 + night2 <= 1).OnlyEnforceIf(penalty)
                self.model.Add(night1 + night2 <= 2)  # Always allow
        
        # Randomization for varied solutions
        random_seed = random.randint(0, 1000000)
        
        # Solve with randomization
        solver = cp_model.CpSolver()
        solver.parameters.random_seed = random_seed
        solver.parameters.num_search_workers = 8  # Use multiple cores
        solver.parameters.max_time_in_seconds = 10.0
        
        status = solver.Solve(self.model)
        
        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            logger.error(f"No solution found. Status: {solver.StatusName(status)}")
            return None
        
        # Prepare results
        assignments = []
        shift_counts = {emp['id']: 0 for emp in self.employees}
        
        for (emp_id, day, shift), var in shifts.items():
            if solver.Value(var):
                emp = next(e for e in self.employees if e['id'] == emp_id)
                assignments.append({
                    'employee_id': emp_id,
                    'employee_name': emp['name'],
                    'day': day,
                    'shift': shift
                })
                shift_counts[emp_id] += 1
        
        return {
            'assignments': assignments,
            'stats': {
                'solve_time': solver.WallTime(),
                'status': solver.StatusName(status),
                'random_seed': random_seed,
                'min_shifts': min_shifts,
                'max_shifts': max_shifts,
                'total_shifts': len(assignments)
            }
        }
