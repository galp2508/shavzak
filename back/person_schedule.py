from typing import List, Tuple, Optional
from assignment_types import AssignmentType

class PersonSchedule():
    """מעקב אחרי לוח הזמנים של כל אדם"""
    def __init__(self, person):
        self.person = person
        self.assignments: List[Tuple[int, int, int, str, AssignmentType]] = []
        
    def add_assignment(self, day: int, start_hour: int, length: int, 
                      assignment_name: str, assignment_type: AssignmentType):
        """הוספת משימה ללוח הזמנים"""
        end_hour = start_hour + length
        self.assignments.append((day, start_hour, end_hour, assignment_name, assignment_type))
        self.assignments.sort(key=lambda x: (x[0], x[1]))
    
    def get_last_assignment(self, day: int = None) -> Optional[Tuple]:
        """מחזיר את המשימה האחרונה"""
        if not self.assignments:
            return None
        
        if day is not None:
            day_assignments = [a for a in self.assignments if a[0] == day]
            if not day_assignments:
                return None
            return max(day_assignments, key=lambda x: x[2])
        
        return max(self.assignments, key=lambda x: (x[0], x[2]))
    
    def can_assign_at(self, day: int, start_hour: int, length: int, 
                     min_rest_hours: int = 8) -> bool:
        """בודק אם אפשר לשבץ משימה בזמן מסוים"""
        end_hour = start_hour + length
        
        for assign_day, assign_start, assign_end, _, _ in self.assignments:
            if assign_day == day:
                if not (end_hour <= assign_start or start_hour >= assign_end):
                    return False
        
        last_assignment = self.get_last_assignment()
        if last_assignment:
            last_day, _, last_end, _, _ = last_assignment
            
            if last_day == day and start_hour < last_end + min_rest_hours:
                return False
            
            if last_day == day - 1:
                hours_since_last = (24 - last_end) + start_hour
                if hours_since_last < min_rest_hours:
                    return False
        
        return True
    
    def get_total_hours(self, day: int = None) -> int:
        """מחזיר סך שעות עבודה"""
        if day is not None:
            return sum(assign[2] - assign[1] for assign in self.assignments 
                      if assign[0] == day)
        return sum(assign[2] - assign[1] for assign in self.assignments)
    
    def get_assignments_by_day(self, day: int) -> List[Tuple]:
        """מחזיר את כל המשימות ביום מסוים"""
        return [a for a in self.assignments if a[0] == day]