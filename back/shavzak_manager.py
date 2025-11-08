from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import copy

class Assignment():
    def __init__(self, name: str, length_in_hours: int, start_hour: int,
                 commanders_needed: int = 0, drivers_needed: int = 0, soldiers_needed: int = 0):
        self.name = name
        self.length_in_hours = length_in_hours
        self.start_hour = start_hour  # 0-23
        self.end_hour = (start_hour + length_in_hours) % 24
        self.commanders_needed = commanders_needed
        self.drivers_needed = drivers_needed
        self.soldiers_needed = soldiers_needed
        self.commanders_assigned = []
        self.drivers_assigned = []
        self.soldiers_assigned = []

    def get_time_range(self) -> str:
        return f"{self.start_hour:02d}:00 - {self.end_hour:02d}:00"

class PersonSchedule():
    """מעקב אחרי לוח הזמנים של כל אדם"""
    def __init__(self, person):
        self.person = person
        self.assignments: List[Tuple[int, int, str]] = []  # (start_hour, end_hour, assignment_name)
        
    def add_assignment(self, start_hour: int, length: int, assignment_name: str):
        end_hour = start_hour + length
        self.assignments.append((start_hour, end_hour, assignment_name))
        self.assignments.sort(key=lambda x: x[0])
    
    def get_last_assignment_end(self) -> Optional[int]:
        """מחזיר את שעת הסיום של המשימה האחרונה"""
        if not self.assignments:
            return None
        return max(assign[1] for assign in self.assignments)
    
    def can_assign_at(self, start_hour: int, length: int, min_rest_hours: int = 8) -> bool:
        """בודק אם אפשר לשבץ משימה בשעה מסוימת"""
        end_hour = start_hour + length
        
        # בדיקת חפיפה עם משימות קיימות
        for assign_start, assign_end, _ in self.assignments:
            if not (end_hour <= assign_start or start_hour >= assign_end):
                return False
        
        # בדיקת זמן מנוחה מינימלי
        last_end = self.get_last_assignment_end()
        if last_end is not None:
            if start_hour < last_end + min_rest_hours and start_hour >= last_end:
                return False
            # אם המשימה הקודמת הסתיימה אחרי חצות
            if last_end > 24 and start_hour < (last_end % 24) + min_rest_hours:
                return False
                
        return True
    
    def get_total_hours(self) -> int:
        """מחזיר סך שעות עבודה"""
        return sum(assign[1] - assign[0] for assign in self.assignments)

class ShavzakManager():
    def __init__(self, pluga_instance):
        self.pluga = pluga_instance
        self.assignment_templates = []  # תבניות משימות
        self.scheduled_assignments = []  # משימות מתוזמנות
        self.min_rest_hours = 8  # מינימום שעות מנוחה
        self.max_work_hours_per_day = 16  # מקסימום שעות עבודה ביום
        
    def get_assignment_template(self):
        """קלט תבניות משימות"""
        while True:
            assignment_name = input("Enter assignment name (or 'exit' to finish): ")
            if assignment_name.lower() == 'exit':
                break
            
            length = int(input("Enter assignment length in hours: "))
            if 24 % length != 0:
                print(f"Warning: {length} hours doesn't divide evenly into 24 hours")
            
            soldiers_needed = int(input("Enter number of soldiers needed: "))
            drivers_needed = int(input("Enter number of drivers needed: "))
            commanders_needed = int(input("Enter number of commanders needed: "))
            
            self.assignment_templates.append({
                'name': assignment_name,
                'length': length,
                'commanders_needed': commanders_needed,
                'drivers_needed': drivers_needed,
                'soldiers_needed': soldiers_needed
            })
    
    def create_time_slots(self):
        """יוצר את כל משבצות הזמן למשימות"""
        self.scheduled_assignments = []
        
        for template in self.assignment_templates:
            slots_per_day = 24 // template['length']
            for slot in range(slots_per_day):
                start_hour = slot * template['length']
                assignment = Assignment(
                    name=template['name'],
                    length_in_hours=template['length'],
                    start_hour=start_hour,
                    commanders_needed=template['commanders_needed'],
                    drivers_needed=template['drivers_needed'],
                    soldiers_needed=template['soldiers_needed']
                )
                self.scheduled_assignments.append(assignment)
        
        # מיון לפי שעת התחלה
        self.scheduled_assignments.sort(key=lambda x: x.start_hour)
    
    def assign_soldiers_smart(self, on_date=None):
        """שיבוץ חכם עם התחשבות בזמני מנוחה"""
        # איסוף כל החיילים הזמינים
        available_soldiers = []
        available_drivers = []
        available_commanders = []
        
        for mahlaka in self.pluga.mahalkot:
            available_soldiers += mahlaka.check_available_soldiers(on_date=on_date)
            available_drivers += mahlaka.check_available_drivers(on_date=on_date)
            available_commanders += mahlaka.check_available_staff(on_date=on_date)
        
        print(f"\n{'='*60}")
        print(f"Starting Smart Assignment Process")
        print(f"{'='*60}")
        print(f"Available: {len(available_commanders)} commanders, {len(available_drivers)} drivers, {len(available_soldiers)} soldiers")
        
        # יצירת מעקב לוח זמנים לכל אדם
        schedules = {}
        for person in available_commanders + available_drivers + available_soldiers:
            schedules[person] = PersonSchedule(person)
        
        # שיבוץ לפי סדר זמנים
        for assignment in self.scheduled_assignments:
            print(f"\n--- Assigning: {assignment.name} ({assignment.get_time_range()}) ---")
            
            # שיבוץ מפקדים
            if not self._assign_role(assignment, 'commander', available_commanders, 
                                    schedules, assignment.commanders_needed):
                raise Exception(
                    f"Failed to assign commanders for {assignment.name} at {assignment.get_time_range()}. "
                    f"Needed {assignment.commanders_needed}, but couldn't find available commanders with enough rest."
                )
            
            # שיבוץ נהגים
            if not self._assign_role(assignment, 'driver', available_drivers, 
                                    schedules, assignment.drivers_needed):
                raise Exception(
                    f"Failed to assign drivers for {assignment.name} at {assignment.get_time_range()}. "
                    f"Needed {assignment.drivers_needed}, but couldn't find available drivers with enough rest."
                )
            
            # שיבוץ חיילים
            if not self._assign_role(assignment, 'soldier', available_soldiers, 
                                    schedules, assignment.soldiers_needed):
                raise Exception(
                    f"Failed to assign soldiers for {assignment.name} at {assignment.get_time_range()}. "
                    f"Needed {assignment.soldiers_needed}, but couldn't find available soldiers with enough rest."
                )
        
        # הדפסת סיכום
        self._print_workload_summary(schedules)
        
        return schedules
    
    def _assign_role(self, assignment: Assignment, role: str, 
                    available_people: List, schedules: Dict, needed: int) -> bool:
        """מנסה לשבץ אנשים לתפקיד מסוים"""
        if needed == 0:
            return True
        
        assigned_list = getattr(assignment, f"{role}s_assigned")
        candidates = []
        
        # מציאת מועמדים זמינים
        for person in available_people:
            if person in assigned_list:
                continue
            
            schedule = schedules[person]
            if schedule.can_assign_at(assignment.start_hour, assignment.length_in_hours, self.min_rest_hours):
                # העדפה למי שעבד פחות
                priority = schedule.get_total_hours()
                candidates.append((priority, person))
        
        # מיון לפי עומס עבודה (פחות שעות = עדיפות גבוהה)
        candidates.sort(key=lambda x: x[0])
        
        # שיבוץ
        assigned_count = 0
        for _, person in candidates:
            if assigned_count >= needed:
                break
            
            assigned_list.append(person)
            schedules[person].add_assignment(
                assignment.start_hour, 
                assignment.length_in_hours, 
                assignment.name
            )
            assigned_count += 1
            print(f"  ✓ Assigned {role}: {person.name} (Total hours: {schedules[person].get_total_hours()})")
        
        return assigned_count >= needed
    
    def _print_workload_summary(self, schedules: Dict):
        """מדפיס סיכום עומסי עבודה"""
        print(f"\n{'='*60}")
        print(f"Workload Summary")
        print(f"{'='*60}")
        
        workloads = [(schedule.person.name, schedule.get_total_hours(), schedule.person.__class__.__name__) 
                     for schedule in schedules.values() if schedule.get_total_hours() > 0]
        workloads.sort(key=lambda x: x[1], reverse=True)
        
        for name, hours, role in workloads:
            print(f"{name:20} ({role:15}): {hours:2} hours")
    
    def display_company_schedule(self):
        """מציג לוח זמנים פלוגתי - מי עושה מה בכל שעה"""
        print(f"\n{'='*80}")
        print(f"📋 COMPANY ASSIGNMENT SCHEDULE - 24 HOUR VIEW")
        print(f"{'='*80}\n")
        
        # קיבוץ משימות לפי שעת התחלה
        time_blocks = {}
        for assignment in self.scheduled_assignments:
            if assignment.start_hour not in time_blocks:
                time_blocks[assignment.start_hour] = []
            time_blocks[assignment.start_hour].append(assignment)
        
        # הצגה לפי סדר זמנים
        for hour in sorted(time_blocks.keys()):
            assignments = time_blocks[hour]
            
            # כותרת בלוק זמן
            end_hour = (hour + assignments[0].length_in_hours) % 24
            print(f"\n⏰ {hour:02d}:00 - {end_hour:02d}:00")
            print(f"{'─'*80}")
            
            # הצגת כל המשימות בבלוק זה
            for assignment in assignments:
                print(f"\n  📌 {assignment.name}")
                
                if assignment.commanders_assigned:
                    print(f"     👨‍✈️  Commanders: {', '.join([c.name for c in assignment.commanders_assigned])}")
                
                if assignment.drivers_assigned:
                    print(f"     🚗 Drivers:    {', '.join([d.name for d in assignment.drivers_assigned])}")
                
                if assignment.soldiers_assigned:
                    print(f"     🪖  Soldiers:   {', '.join([s.name for s in assignment.soldiers_assigned])}")
            
            print()  # שורה ריקה בין בלוקים


# דוגמת שימוש
if __name__ == "__main__":
    # יצירת דוגמה
    print("Smart Assignment Scheduler with Rest Periods")
    print("=" * 60)
    print("\nFeatures:")
    print("- Minimum 8 hours rest between assignments")
    print("- Balanced workload distribution")
    print("- Company-wide schedule view")
    print("- Conflict detection")
    print("\nReady to use with your pluga instance!")