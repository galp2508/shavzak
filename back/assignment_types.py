from enum import Enum

class AssignmentType(Enum):
    """סוגי משימות"""
    PATROL = "סיור"
    GUARD = "שמירה"
    STANDBY_A = "כוננות א"
    STANDBY_B = "כוננות ב"
    OPERATIONS = "חמל"
    KITCHEN = "תורן מטבח"
    HAFAK_GASHASH = "חפ״ק גשש"
    SHALAZ = "של״ז"
    DUTY_OFFICER = "קצין תורן"

class Assignment():
    def __init__(self, name: str, assignment_type: AssignmentType, 
                 length_in_hours: int, start_hour: int, day: int = 0):
        self.name = name
        self.type = assignment_type
        self.length_in_hours = length_in_hours
        self.start_hour = start_hour
        self.day = day
        self.end_hour = (start_hour + length_in_hours) % 24
        
        self._set_requirements()
        
        self.commanders_assigned = []
        self.drivers_assigned = []
        self.soldiers_assigned = []
        self.assigned_mahlaka = None
        self.prefer_from_previous = None
    
    def _set_requirements(self):
        """הגדרת דרישות לפי סוג המשימה"""
        if self.type == AssignmentType.PATROL:
            self.commanders_needed = 1
            self.drivers_needed = 1
            self.soldiers_needed = 2
            self.same_mahlaka_required = True
            self.requires_certification = None
            self.only_soldiers = False
            
        elif self.type == AssignmentType.GUARD:
            self.commanders_needed = 0
            self.drivers_needed = 0
            self.soldiers_needed = 1
            self.same_mahlaka_required = False
            self.requires_certification = None
            self.only_soldiers = True
            self.is_short_shift = True
            
        elif self.type == AssignmentType.STANDBY_A:
            self.commanders_needed = 1
            self.drivers_needed = 1
            self.soldiers_needed = 7
            self.same_mahlaka_required = False
            self.requires_certification = None
            self.only_soldiers = False
            
        elif self.type == AssignmentType.STANDBY_B:
            self.commanders_needed = 1
            self.drivers_needed = 0
            self.soldiers_needed = 3
            self.same_mahlaka_required = False
            self.requires_certification = None
            self.only_soldiers = False
            
        elif self.type == AssignmentType.OPERATIONS:
            self.commanders_needed = 0
            self.drivers_needed = 0
            self.soldiers_needed = 1
            self.same_mahlaka_required = False
            self.requires_certification = "חמל"
            self.only_soldiers = False
            
        elif self.type == AssignmentType.KITCHEN:
            self.commanders_needed = 0
            self.drivers_needed = 0
            self.soldiers_needed = 1
            self.same_mahlaka_required = False
            self.requires_certification = None
            self.only_soldiers = True
            self.is_daily_assignment = True
            
        elif self.type == AssignmentType.HAFAK_GASHASH:
            self.commanders_needed = 0
            self.drivers_needed = 0
            self.soldiers_needed = 1
            self.same_mahlaka_required = False
            self.requires_certification = None
            self.only_soldiers = False
            self.allow_commander = True
            self.prefer_same_person_all_day = True
            
        elif self.type == AssignmentType.SHALAZ:
            self.commanders_needed = 0
            self.drivers_needed = 0
            self.soldiers_needed = 1
            self.same_mahlaka_required = False
            self.requires_certification = None
            self.only_soldiers = True
            self.is_daily_assignment = True
            
        elif self.type == AssignmentType.DUTY_OFFICER:
            self.commanders_needed = 1
            self.drivers_needed = 0
            self.soldiers_needed = 0
            self.same_mahlaka_required = False
            self.requires_certification = None
            self.only_soldiers = False
            self.requires_senior_commander = True
    
    def get_time_range(self) -> str:
        return f"{self.start_hour:02d}:00 - {self.end_hour:02d}:00"
    
    def get_full_time_info(self) -> str:
        """מחזיר מידע מלא על זמן כולל יום"""
        day_str = f"יום {self.day + 1}" if self.day > 0 else "היום"
        return f"{day_str} {self.get_time_range()}"