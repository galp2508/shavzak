from typing import Dict, List
from person_schedule import PersonSchedule
from assignment_types import Assignment

class ShavzakValidator:
    """בודק תקינות של שיבוץ"""
    
    def __init__(self, min_rest_hours: int = 8, max_hours_per_day: int = None):
        self.min_rest_hours = min_rest_hours
        self.max_hours_per_day = max_hours_per_day
        self.errors = []
        self.warnings = []
    
    def validate_schedule(self, schedules: Dict[object, PersonSchedule], 
                         assignments: List[Assignment]) -> bool:
        """בדיקה מלאה של השיבוץ"""
        self.errors = []
        self.warnings = []
        
        self._check_all_assignments_filled(assignments)
        self._check_no_overlaps(schedules)
        self._check_rest_periods(schedules)
        
        if self.max_hours_per_day:
            self._check_daily_hours(schedules)
        
        self._print_results()
        
        return len(self.errors) == 0
    
    def _check_all_assignments_filled(self, assignments: List[Assignment]):
        """בודק שכל המשימות מאוישות"""
        for assign in assignments:
            if len(assign.commanders_assigned) < assign.commanders_needed:
                self.errors.append(
                    f"❌ {assign.name} ביום {assign.day + 1}: חסרים מפקדים "
                    f"({len(assign.commanders_assigned)}/{assign.commanders_needed})"
                )
            
            if len(assign.drivers_assigned) < assign.drivers_needed:
                self.errors.append(
                    f"❌ {assign.name} ביום {assign.day + 1}: חסרים נהגים "
                    f"({len(assign.drivers_assigned)}/{assign.drivers_needed})"
                )
            
            if len(assign.soldiers_assigned) < assign.soldiers_needed:
                self.errors.append(
                    f"❌ {assign.name} ביום {assign.day + 1}: חסרים חיילים "
                    f"({len(assign.soldiers_assigned)}/{assign.soldiers_needed})"
                )
    
    def _check_no_overlaps(self, schedules: Dict):
        """בודק שאין חפיפות בלוחות זמנים"""
        for person, schedule in schedules.items():
            assignments = schedule.assignments
            for i in range(len(assignments)):
                for j in range(i + 1, len(assignments)):
                    day1, start1, end1, name1, _ = assignments[i]
                    day2, start2, end2, name2, _ = assignments[j]
                    
                    if day1 == day2:
                        if not (end1 <= start2 or end2 <= start1):
                            self.errors.append(
                                f"❌ {person.name} - חפיפה ביום {day1 + 1}: "
                                f"{name1} ({start1:02d}:00-{end1:02d}:00) ו-"
                                f"{name2} ({start2:02d}:00-{end2:02d}:00)"
                            )
    
    def _check_rest_periods(self, schedules: Dict):
        """בודק זמני מנוחה מינימליים"""
        for person, schedule in schedules.items():
            assignments = sorted(schedule.assignments, key=lambda x: (x[0], x[1]))
            
            for i in range(len(assignments) - 1):
                day1, _, end1, name1, _ = assignments[i]
                day2, start2, _, name2, _ = assignments[i + 1]
                
                if day1 == day2:
                    rest = start2 - end1
                    if rest < self.min_rest_hours:
                        self.warnings.append(
                            f"⚠️  {person.name} - מנוחה קצרה ביום {day1 + 1}: "
                            f"{rest} שעות בין {name1} ל-{name2} "
                            f"(מינימום: {self.min_rest_hours})"
                        )
                
                elif day2 == day1 + 1:
                    rest = (24 - end1) + start2
                    if rest < self.min_rest_hours:
                        self.warnings.append(
                            f"⚠️  {person.name} - מנוחה קצרה בין יום {day1 + 1} ליום {day2 + 1}: "
                            f"{rest} שעות בין {name1} ל-{name2}"
                        )
    
    def _check_daily_hours(self, schedules: Dict):
        """בודק שלא עובדים יותר מדי שעות ביום"""
        for person, schedule in schedules.items():
            days = set(a[0] for a in schedule.assignments)
            
            for day in days:
                hours = schedule.get_total_hours(day)
                if hours > self.max_hours_per_day:
                    self.warnings.append(
                        f"⚠️  {person.name} - יותר מדי שעות ביום {day + 1}: "
                        f"{hours} שעות (מקסימום מומלץ: {self.max_hours_per_day})"
                    )
    
    def _print_results(self):
        """מדפיס תוצאות הבדיקה"""
        print(f"\n{'='*70}")
        print("🔍 תוצאות בדיקת תקינות")
        print(f"{'='*70}\n")
        
        if not self.errors and not self.warnings:
            print("✅ השיבוץ תקין לחלוטין!")
            return
        
        if self.errors:
            print(f"❌ נמצאו {len(self.errors)} שגיאות:\n")
            for error in self.errors:
                print(error)
        
        if self.warnings:
            print(f"\n⚠️  נמצאו {len(self.warnings)} אזהרות:\n")
            for warning in self.warnings:
                print(warning)