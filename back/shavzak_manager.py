from datetime import datetime, timedelta
from typing import List, Dict
from assignment_types import Assignment, AssignmentType
from person_schedule import PersonSchedule
from assignment_logic import AssignmentLogic

class shavzak_manager():
    def __init__(self, pluga_instance, days_ahead: int = 7):
        self.pluga = pluga_instance
        self.days_ahead = days_ahead
        self.assignment_templates = []
        self.scheduled_assignments = []
        self.min_rest_hours = 8
        self.max_work_hours_per_day = None
        self.shift_length = 8
        self.logic = AssignmentLogic(min_rest_hours=self.min_rest_hours)
        
    def setup_default_assignments(self):
        """הגדרת משימות ברירת מחדל"""
        print("\n📋 Setting up default assignment types:")
        print("=" * 70)
        
        self.add_assignment_template("סיור", AssignmentType.PATROL, 8, 3)
        print("✓ סיור: נהג + מפקד + 2 לוחמים (3x8 שעות)")
        
        self.add_assignment_template("שמירה", AssignmentType.GUARD, 4, 6)
        print("✓ שמירה: חייל אחד (6x4 שעות)")
        
        self.add_assignment_template("כוננות א", AssignmentType.STANDBY_A, 8, 3)
        print("✓ כוננות א: מפקד + נהג + 7 חיילים (3x8 שעות)")
        
        self.add_assignment_template("כוננות ב", AssignmentType.STANDBY_B, 8, 3)
        print("✓ כוננות ב: מפקד + 3 חיילים (3x8 שעות)")
        
        self.add_assignment_template("חמל", AssignmentType.OPERATIONS, 12, 2)
        print("✓ חמל: מוסמך חמל (2x12 שעות)")
        
        self.add_assignment_template("תורן מטבח", AssignmentType.KITCHEN, 24, 1)
        print("✓ תורן מטבח: חייל אחד (24 שעות - כל היום)")
        
        self.add_assignment_template("חפ״ק גשש", AssignmentType.HAFAK_GASHASH, 12, 2)
        print("✓ חפ״ק גשש: לוחם או מפקד (2x12 שעות)")
        
        self.add_assignment_template("של״ז", AssignmentType.SHALAZ, 24, 1)
        print("✓ של״ז: לוחם (24 שעות - כל היום)")
        
        self.add_assignment_template("קצין תורן", AssignmentType.DUTY_OFFICER, 24, 1)
        print("✓ קצין תורן: מפקד בכיר (24 שעות)")
    
    def add_assignment_template(self, name: str, assignment_type: AssignmentType, 
                                length_in_hours: int, times_per_day: int = None):
        """הוספת תבנית משימה"""
        if times_per_day is None:
            times_per_day = 24 // length_in_hours
        
        self.assignment_templates.append({
            'name': name,
            'type': assignment_type,
            'length': length_in_hours,
            'times_per_day': times_per_day
        })
    
    def validate_manpower_requirements(self):
        """בדיקה שיש מספיק כוח אדם לכל המשימות"""
        print(f"\n{'='*70}")
        print("🔍 בדיקת דרישות כוח אדם")
        print(f"{'='*70}\n")
        
        daily_commanders = 0
        daily_drivers = 0
        daily_soldiers = 0
        
        for template in self.assignment_templates:
            times = template['times_per_day']
            assign_type = template['type']
            
            dummy = Assignment("dummy", assign_type, template['length'], 0, 0)
            
            daily_commanders += dummy.commanders_needed * times
            daily_drivers += dummy.drivers_needed * times
            daily_soldiers += dummy.soldiers_needed * times
        
        total_commanders = 0
        total_drivers = 0
        total_soldiers = 0
        
        for mahlaka in self.pluga.mahalkot:
            total_commanders += len(mahlaka.staff)
            total_drivers += len(mahlaka.drivers)
            total_soldiers += len(mahlaka.soldiers)
        
        print(f"דרישות יומיות (במקביל):")
        print(f"  מפקדים:  {daily_commanders} נדרשים")
        print(f"  נהגים:   {daily_drivers} נדרשים")
        print(f"  חיילים:  {daily_soldiers} נדרשים")
        
        print(f"\nכוח אדם זמין:")
        print(f"  מפקדים:  {total_commanders} זמינים")
        print(f"  נהגים:   {total_drivers} זמינים")
        print(f"  חיילים:  {total_soldiers} זמינים")
        
        issues = []
        if total_commanders < daily_commanders:
            issues.append(f"⚠️  חסרים {daily_commanders - total_commanders} מפקדים")
        if total_drivers < daily_drivers:
            issues.append(f"⚠️  חסרים {daily_drivers - total_drivers} נהגים")
        if total_soldiers < daily_soldiers:
            issues.append(f"⚠️  חסרים {daily_soldiers - total_soldiers} חיילים")
        
        if issues:
            print(f"\n❌ בעיות זוהו:")
            for issue in issues:
                print(f"  {issue}")
            print(f"\nאזהרה: השיבוץ עלול להיכשל בגלל מחסור בכוח אדם!")
            
            response = input("\nלהמשיך בכל זאת? (y/n): ")
            if response.lower() != 'y':
                raise Exception("השיבוץ בוטל על ידי המשתמש")
        else:
            print(f"\n✅ יש מספיק כוח אדם לכל המשימות!")
    
    def create_time_slots(self):
        """יוצר משבצות זמן לכמה ימים קדימה"""
        self.scheduled_assignments = []
        num_mahalkot = len(self.pluga.mahalkot)
        
        for day in range(self.days_ahead):
            for template in self.assignment_templates:
                for slot in range(template['times_per_day']):
                    start_hour = slot * template['length']
                    
                    assign = Assignment(
                        name=f"{template['name']} {slot + 1}",
                        assignment_type=template['type'],
                        length_in_hours=template['length'],
                        start_hour=start_hour,
                        day=day
                    )
                    
                    if assign.same_mahlaka_required and num_mahalkot > 0:
                        preferred_mahlaka_index = (day * 3 + slot) % num_mahalkot
                        assign.preferred_mahlaka = self.pluga.mahalkot[preferred_mahlaka_index]
                    
                    self.scheduled_assignments.append(assign)
        
        self.scheduled_assignments.sort(key=lambda x: (x.day, x.start_hour))
        self._link_standby_to_previous()
        
        print(f"\n✓ נוצרו {len(self.scheduled_assignments)} משימות ל-{self.days_ahead} ימים")
    
    def _link_standby_to_previous(self):
        """מקשר כוננויות למשימות קודמות"""
        for i, assign in enumerate(self.scheduled_assignments):
            if assign.type == AssignmentType.STANDBY_A:
                for prev in self.scheduled_assignments[:i]:
                    if prev.type == AssignmentType.PATROL and prev.day == assign.day and \
                       prev.end_hour == assign.start_hour:
                        assign.prefer_from_previous = prev
                        break
            
            elif assign.type == AssignmentType.STANDBY_B:
                for prev in self.scheduled_assignments[:i]:
                    if prev.day == assign.day and prev.end_hour == assign.start_hour:
                        if prev.type in [AssignmentType.GUARD, AssignmentType.PATROL]:
                            assign.prefer_from_previous = prev
                            break
    def assign_soldiers_smart(self, start_date=None):
        """שיבוץ חכם - תמיד מצליח!"""
        mahalkot_data = []
        for mahlaka in self.pluga.mahalkot:
            mahlaka_info = {
                'mahlaka': mahlaka,
                'soldiers': mahlaka.check_available_soldiers(on_date=start_date, strict=True),
                'drivers': mahlaka.check_available_drivers(on_date=start_date, strict=True),
                'commanders': mahlaka.check_available_staff(on_date=start_date, strict=True)
            }
            mahalkot_data.append(mahlaka_info)
        
        all_commanders = []
        all_drivers = []
        all_soldiers = []
        
        for mahlaka_info in mahalkot_data:
            all_commanders += mahlaka_info['commanders']
            all_drivers += mahlaka_info['drivers']
            all_soldiers += mahlaka_info['soldiers']
        
        print(f"\n{'='*70}")
        print(f"🎖️  SMART ASSIGNMENT - {self.days_ahead} DAYS")
        print(f"{'='*70}")
        print(f"זמינים (strict): {len(all_commanders)} מפקדים, {len(all_drivers)} נהגים, {len(all_soldiers)} חיילים")
        print(f"מינימום מנוחה: {self.min_rest_hours} שעות")
        print(f"⭐ אין מקסימום שעות עבודה - העיקר הוגנות!\n")
        
        schedules = {}
        for person in all_commanders + all_drivers + all_soldiers:
            schedules[person] = PersonSchedule(person)
        
        mahlaka_workload = {info['mahlaka']: 0 for info in mahalkot_data}
        
        failed_assignments = []
        for assign in self.scheduled_assignments:
            print(f"\n{'─'*70}")
            print(f"📅 {assign.get_full_time_info()} | {assign.name}")
            
            try:
                self._assign_by_type(assign, mahalkot_data, all_commanders, 
                                    all_drivers, all_soldiers, schedules, mahlaka_workload)
            except Exception as e:
                print(f"  ❌ {e}")
                failed_assignments.append(assign)
        
        if failed_assignments:
            print(f"\n{'='*70}")
            print(f"⚠️  נמצאו {len(failed_assignments)} משימות שנכשלו")
            print(f"{'='*70}")
            print("מנסה שוב עם הקלות...")
            
            for mahlaka_info in mahalkot_data:
                mahlaka_info['soldiers'] += mahlaka_info['mahlaka'].check_available_soldiers(on_date=start_date, strict=False)
                mahlaka_info['drivers'] += mahlaka_info['mahlaka'].check_available_drivers(on_date=start_date, strict=False)
                mahlaka_info['commanders'] += mahlaka_info['mahlaka'].check_available_staff(on_date=start_date, strict=False)
                mahlaka_info['soldiers'] = list(set(mahlaka_info['soldiers']))
                mahlaka_info['drivers'] = list(set(mahlaka_info['drivers']))
                mahlaka_info['commanders'] = list(set(mahlaka_info['commanders']))
            
            self.logic.enable_emergency_mode()
            
            for assign in failed_assignments:
                print(f"\n📅 מנסה שוב: {assign.get_full_time_info()} | {assign.name}")
                try:
                    self._assign_by_type(assign, mahalkot_data, all_commanders, 
                                        all_drivers, all_soldiers, schedules, mahlaka_workload)
                    print(f"  ✅ הצליח במצב חירום!")
                except Exception as e:
                    print(f"  ❌ עדיין נכשל: {e}")
        
        self._print_summary(schedules, mahlaka_workload)
        self._print_fairness_analysis(schedules)
        
        if self.logic.warnings:
            print(f"\n{'='*70}")
            print(f"⚠️  WARNINGS - {len(self.logic.warnings)} אזהרות")
            print(f"{'='*70}")
            for warning in self.logic.warnings:
                print(warning)
        
        print(f"\n✅ שיבוץ הושלם בהצלחה!")
        return schedules

    def _assign_by_type(self, assign, mahalkot_data, all_commanders, 
                        all_drivers, all_soldiers, schedules, mahlaka_workload):
        """מפנה לפונקציית השיבוץ המתאימה"""
        if assign.type == AssignmentType.PATROL:
            self.logic.assign_patrol(assign, mahalkot_data, schedules, mahlaka_workload)
        elif assign.type == AssignmentType.GUARD:
            self.logic.assign_guard(assign, all_soldiers, schedules)
        elif assign.type == AssignmentType.STANDBY_A:
            self.logic.assign_standby_a(assign, all_commanders, all_drivers, 
                                       all_soldiers, schedules)
        elif assign.type == AssignmentType.STANDBY_B:
            self.logic.assign_standby_b(assign, all_commanders, all_soldiers, schedules)
        elif assign.type == AssignmentType.OPERATIONS:
            self.logic.assign_operations(assign, all_commanders + all_soldiers, schedules)
        elif assign.type == AssignmentType.KITCHEN:
            self.logic.assign_kitchen(assign, all_soldiers, schedules)
        elif assign.type == AssignmentType.HAFAK_GASHASH:
            self.logic.assign_hafak_gashash(assign, all_commanders, all_soldiers, schedules)
        elif assign.type == AssignmentType.SHALAZ:
            self.logic.assign_shalaz(assign, all_soldiers, schedules)
        elif assign.type == AssignmentType.DUTY_OFFICER:
            self.logic.assign_duty_officer(assign, all_commanders, schedules)
    
    def _print_summary(self, schedules: Dict, mahlaka_workload: Dict):
        """סיכום"""
        print(f"\n{'='*70}")
        print(f"📊 SUMMARY")
        print(f"{'='*70}\n")
        
        for day in range(min(3, self.days_ahead)):
            print(f"\n--- יום {day + 1} ---")
            workloads = [(s.person.name, s.get_total_hours(day), s.person.role) 
                        for s in schedules.values() if s.get_total_hours(day) > 0]
            workloads.sort(key=lambda x: x[1], reverse=True)
            
            for name, hours, role in workloads[:10]:
                print(f"{name:20} ({role:15}): {hours:2} שעות")
    
    def _print_fairness_analysis(self, schedules: Dict):
        """ניתוח הוגנות השיבוץ"""
        print(f"\n{'='*70}")
        print(f"⚖️  FAIRNESS ANALYSIS")
        print(f"{'='*70}\n")
        
        total_hours = {}
        for person, schedule in schedules.items():
            hours = schedule.get_total_hours()
            if hours > 0:
                total_hours[person.name] = {
                    'hours': hours,
                    'role': person.role,
                    'avg_per_day': hours / self.days_ahead
                }
        
        if not total_hours:
            print("אין נתונים להצגה")
            return
        
        hours_list = [d['hours'] for d in total_hours.values()]
        avg = sum(hours_list) / len(hours_list)
        min_hours = min(hours_list)
        max_hours = max(hours_list)
        
        print(f"📊 סטטיסטיקה כללית:")
        print(f"  ממוצע שעות לחייל: {avg:.1f} שעות")
        print(f"  מינימום: {min_hours} שעות")
        print(f"  מקסימום: {max_hours} שעות")
        print(f"  הפרש (מקס-מין): {max_hours - min_hours} שעות")
        
        acceptable_diff = avg * 0.2
        if (max_hours - min_hours) <= acceptable_diff:
            print(f"\n✅ השיבוץ הוגן! הפרש קטן בין מקסימום למינימום")
        else:
            print(f"\n⚠️  יש הפרש משמעותי בין העומסים")
        
        print(f"\n🏆 5 הכי עסוקים:")
        sorted_workers = sorted(total_hours.items(), key=lambda x: x[1]['hours'], reverse=True)
        for i, (name, data) in enumerate(sorted_workers[:5], 1):
            print(f"  {i}. {name:20} | {data['hours']:3} שעות | {data['avg_per_day']:.1f}/יום")
        
        print(f"\n💤 5 הכי פחות עסוקים:")
        for i, (name, data) in enumerate(list(reversed(sorted_workers))[:5], 1):
            print(f"  {i}. {name:20} | {data['hours']:3} שעות | {data['avg_per_day']:.1f}/יום")
    
    def display_company_schedule(self, day: int = None):
        """הצגת לוח זמנים"""
        if day is not None:
            assignments_to_show = [a for a in self.scheduled_assignments if a.day == day]
            print(f"\n{'='*80}")
            print(f"📋 SCHEDULE - יום {day + 1}")
            print(f"{'='*80}\n")
        else:
            assignments_to_show = self.scheduled_assignments
            print(f"\n{'='*80}")
            print(f"📋 FULL SCHEDULE - {self.days_ahead} DAYS")
            print(f"{'='*80}\n")
        
        current_day = None
        time_blocks = {}
        
        for assign in assignments_to_show:
            if current_day != assign.day:
                if time_blocks:
                    self._print_day_schedule(current_day, time_blocks)
                current_day = assign.day
                time_blocks = {}
            
            key = (assign.day, assign.start_hour)
            if key not in time_blocks:
                time_blocks[key] = []
            time_blocks[key].append(assign)
        
        if time_blocks:
            self._print_day_schedule(current_day, time_blocks)
    
    def _print_day_schedule(self, day: int, time_blocks: Dict):
        """מדפיס לוח זמנים של יום אחד"""
        print(f"\n{'─'*80}")
        print(f"📅 יום {day + 1}")
        print(f"{'─'*80}")
        
        for (_, hour), assignments in sorted(time_blocks.items()):
            if not assignments:
                continue
            
            end_hour = (hour + assignments[0].length_in_hours) % 24
            
            if assignments[0].length_in_hours == 24:
                print(f"\n⏰ כל היום (24 שעות)")
            else:
                print(f"\n⏰ {hour:02d}:00 - {end_hour:02d}:00")
            
            for assign in assignments:
                mahlaka_str = f" [מחלקה {assign.assigned_mahlaka.number}]" if assign.assigned_mahlaka else ""
                print(f"  📌 {assign.name} ({assign.type.value}){mahlaka_str}")
                
                if assign.commanders_assigned:
                    print(f"     👨‍✈️  {', '.join([c.name for c in assign.commanders_assigned])}")
                if assign.drivers_assigned:
                    print(f"     🚗 {', '.join([d.name for d in assign.drivers_assigned])}")
                if assign.soldiers_assigned:
                    print(f"     🪖  {', '.join([s.name for s in assign.soldiers_assigned])}")