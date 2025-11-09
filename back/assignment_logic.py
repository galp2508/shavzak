from typing import List, Dict
from assignment_types import Assignment, AssignmentType
from person_schedule import PersonSchedule

class AssignmentLogic:
    """לוגיקת שיבוץ למשימות שונות - עם מצב חירום"""
    
    def __init__(self, min_rest_hours: int = 8):
        self.min_rest_hours = min_rest_hours
        self.emergency_mode = False
        self.warnings = []
    
    def enable_emergency_mode(self):
        """הפעלת מצב חירום - המערכת תמצא פתרון בכל מחיר"""
        self.emergency_mode = True
        print("\n⚠️  מצב חירום הופעל - המערכת תמצא פתרון גם במחסור בכוח אדם")
    
    def assign_patrol(self, assign: Assignment, mahalkot_data: List[Dict], 
                     schedules: Dict, mahlaka_workload: Dict):
        """שיבוץ סיור - מחלקה שלמה"""
        result = self._try_assign_patrol_normal(assign, mahalkot_data, schedules, mahlaka_workload)
        if result:
            return True
        
        if self.emergency_mode:
            return self._try_assign_patrol_emergency(assign, mahalkot_data, schedules, mahlaka_workload)
        
        raise Exception(f"לא נמצאה מחלקה זמינה לסיור ב-{assign.get_full_time_info()}")
    
    def _try_assign_patrol_normal(self, assign, mahalkot_data, schedules, mahlaka_workload):
        """ניסיון רגיל לשיבוץ סיור"""
        mahalkot_sorted = self._sort_mahalkot_by_preference(assign, mahalkot_data, mahlaka_workload)
        
        for mahlaka_info in mahalkot_sorted:
            available_commanders = [c for c in mahlaka_info['commanders'] 
                                   if schedules[c].can_assign_at(assign.day, assign.start_hour, 
                                                                 assign.length_in_hours, self.min_rest_hours)]
            available_drivers = [d for d in mahlaka_info['drivers'] 
                                if schedules[d].can_assign_at(assign.day, assign.start_hour, 
                                                              assign.length_in_hours, self.min_rest_hours)]
            available_soldiers = [s for s in mahlaka_info['soldiers'] 
                                 if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                               assign.length_in_hours, self.min_rest_hours)]
            
            if len(available_commanders) >= 1 and len(available_drivers) >= 1 and \
               len(available_soldiers) >= 2:
                self._do_assign(assign, available_commanders[:1], schedules, 'commander')
                self._do_assign(assign, available_drivers[:1], schedules, 'driver')
                self._do_assign(assign, available_soldiers[:2], schedules, 'soldier')
                
                assign.assigned_mahlaka = mahlaka_info['mahlaka']
                mahlaka_workload[mahlaka_info['mahlaka']] += assign.length_in_hours
                
                print(f"  ✓ מחלקה {mahlaka_info['mahlaka'].number}")
                return True
        
        return False
    
    def _try_assign_patrol_emergency(self, assign, mahalkot_data, schedules, mahlaka_workload):
        """ניסיון חירום - מקל על הדרישות"""
        print(f"  ⚠️  מצב חירום: מנסה למצוא פתרון עם הקלות")
        
        reduced_rest = self.min_rest_hours // 2
        for mahlaka_info in mahalkot_data:
            available_commanders = [c for c in mahlaka_info['commanders'] 
                                   if schedules[c].can_assign_at(assign.day, assign.start_hour, 
                                                                 assign.length_in_hours, reduced_rest)]
            available_drivers = [d for d in mahlaka_info['drivers'] 
                                if schedules[d].can_assign_at(assign.day, assign.start_hour, 
                                                              assign.length_in_hours, reduced_rest)]
            available_soldiers = [s for s in mahlaka_info['soldiers'] 
                                 if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                               assign.length_in_hours, reduced_rest)]
            
            if len(available_commanders) >= 1 and len(available_drivers) >= 1 and \
               len(available_soldiers) >= 2:
                self._do_assign(assign, available_commanders[:1], schedules, 'commander')
                self._do_assign(assign, available_drivers[:1], schedules, 'driver')
                self._do_assign(assign, available_soldiers[:2], schedules, 'soldier')
                
                assign.assigned_mahlaka = mahlaka_info['mahlaka']
                mahlaka_workload[mahlaka_info['mahlaka']] += assign.length_in_hours
                
                self.warnings.append(f"⚠️  {assign.name}: מנוחה מופחתת ל-{reduced_rest} שעות")
                print(f"  ⚠️  מחלקה {mahlaka_info['mahlaka'].number} (מנוחה מופחתת)")
                return True
        
        all_commanders = [c for info in mahalkot_data for c in info['commanders']]
        all_drivers = [d for info in mahalkot_data for d in info['drivers']]
        all_soldiers = [s for info in mahalkot_data for s in info['soldiers']]
        
        available_commanders = [c for c in all_commanders 
                               if schedules[c].can_assign_at(assign.day, assign.start_hour, 
                                                             assign.length_in_hours, reduced_rest)]
        available_drivers = [d for d in all_drivers 
                            if schedules[d].can_assign_at(assign.day, assign.start_hour, 
                                                          assign.length_in_hours, reduced_rest)]
        available_soldiers = [s for s in all_soldiers 
                             if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                           assign.length_in_hours, reduced_rest)]
        
        if len(available_commanders) >= 1 and len(available_drivers) >= 1 and \
           len(available_soldiers) >= 2:
            self._do_assign(assign, available_commanders[:1], schedules, 'commander')
            self._do_assign(assign, available_drivers[:1], schedules, 'driver')
            self._do_assign(assign, available_soldiers[:2], schedules, 'soldier')
            
            self.warnings.append(f"⚠️  {assign.name}: ערבוב מחלקות + מנוחה מופחתת")
            print(f"  ⚠️  ערבוב מחלקות (חירום)")
            return True
        
        return False
    
    def _sort_mahalkot_by_preference(self, assign, mahalkot_data, mahlaka_workload):
        """מיון מחלקות לפי העדפה"""
        if hasattr(assign, 'preferred_mahlaka') and assign.preferred_mahlaka:
            mahalkot_sorted = [info for info in mahalkot_data 
                              if info['mahlaka'] == assign.preferred_mahlaka]
            mahalkot_sorted += [info for info in mahalkot_data 
                               if info['mahlaka'] != assign.preferred_mahlaka]
        else:
            mahalkot_sorted = sorted(mahalkot_data, 
                                    key=lambda x: mahlaka_workload[x['mahlaka']])
        return mahalkot_sorted
    
    def assign_guard(self, assign: Assignment, all_soldiers: List, schedules: Dict):
        """שיבוץ שמירה"""
        available = [s for s in all_soldiers 
                    if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                  assign.length_in_hours, self.min_rest_hours)]
        available.sort(key=lambda x: schedules[x].get_total_hours())
        
        if len(available) >= 1:
            self._do_assign(assign, [available[0]], schedules, 'soldier')
            return True
        
        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            available = [s for s in all_soldiers 
                        if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                      assign.length_in_hours, reduced_rest)]
            if len(available) >= 1:
                self._do_assign(assign, [available[0]], schedules, 'soldier')
                self.warnings.append(f"⚠️  {assign.name}: מנוחה מופחתת")
                print(f"  ⚠️  מנוחה מופחתת")
                return True
        
        raise Exception(f"אין חייל זמין לשמירה ב-{assign.get_full_time_info()}")
    def assign_standby_a(self, assign: Assignment, all_commanders: List, 
                        all_drivers: List, all_soldiers: List, schedules: Dict):
        """כוננות א"""
        preferred_people = []
        if assign.prefer_from_previous:
            prev = assign.prefer_from_previous
            preferred_people = prev.commanders_assigned + prev.drivers_assigned + prev.soldiers_assigned
        
        available_commanders = [c for c in all_commanders 
                               if schedules[c].can_assign_at(assign.day, assign.start_hour, 
                                                             assign.length_in_hours, self.min_rest_hours)]
        available_drivers = [d for d in all_drivers 
                            if schedules[d].can_assign_at(assign.day, assign.start_hour, 
                                                          assign.length_in_hours, self.min_rest_hours)]
        available_soldiers = [s for s in all_soldiers 
                             if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                           assign.length_in_hours, self.min_rest_hours)]
        
        if preferred_people:
            available_commanders.sort(key=lambda x: 0 if x in preferred_people else 1)
            available_drivers.sort(key=lambda x: 0 if x in preferred_people else 1)
            available_soldiers.sort(key=lambda x: 0 if x in preferred_people else 1)
        else:
            available_commanders.sort(key=lambda x: schedules[x].get_total_hours())
            available_drivers.sort(key=lambda x: schedules[x].get_total_hours())
            available_soldiers.sort(key=lambda x: schedules[x].get_total_hours())
        
        if len(available_commanders) >= 1 and len(available_drivers) >= 1 and len(available_soldiers) >= 7:
            self._do_assign(assign, [available_commanders[0]], schedules, 'commander')
            self._do_assign(assign, [available_drivers[0]], schedules, 'driver')
            self._do_assign(assign, available_soldiers[:7], schedules, 'soldier')
            return True
        
        if self.emergency_mode:
            min_soldiers = min(len(available_soldiers), 5)
            if len(available_commanders) >= 1 and len(available_drivers) >= 1 and len(available_soldiers) >= min_soldiers:
                self._do_assign(assign, [available_commanders[0]], schedules, 'commander')
                self._do_assign(assign, [available_drivers[0]], schedules, 'driver')
                self._do_assign(assign, available_soldiers[:min_soldiers], schedules, 'soldier')
                self.warnings.append(f"⚠️  {assign.name}: רק {min_soldiers} חיילים במקום 7")
                print(f"  ⚠️  רק {min_soldiers} חיילים")
                return True
        
        raise Exception(f"אין מספיק כוח אדם לכוננות א ב-{assign.get_full_time_info()}")
    
    def assign_standby_b(self, assign: Assignment, all_commanders: List, 
                        all_soldiers: List, schedules: Dict):
        """כוננות ב"""
        preferred_people = []
        if assign.prefer_from_previous:
            prev = assign.prefer_from_previous
            preferred_people = prev.commanders_assigned + prev.soldiers_assigned
        
        available_commanders = [c for c in all_commanders 
                               if schedules[c].can_assign_at(assign.day, assign.start_hour, 
                                                             assign.length_in_hours, self.min_rest_hours)]
        available_soldiers = [s for s in all_soldiers 
                             if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                           assign.length_in_hours, self.min_rest_hours)]
        
        if preferred_people:
            available_commanders.sort(key=lambda x: 0 if x in preferred_people else 1)
            available_soldiers.sort(key=lambda x: 0 if x in preferred_people else 1)
        else:
            available_commanders.sort(key=lambda x: schedules[x].get_total_hours())
            available_soldiers.sort(key=lambda x: schedules[x].get_total_hours())
        
        if len(available_commanders) >= 1 and len(available_soldiers) >= 3:
            self._do_assign(assign, [available_commanders[0]], schedules, 'commander')
            self._do_assign(assign, available_soldiers[:3], schedules, 'soldier')
            return True
        
        if self.emergency_mode:
            min_soldiers = min(len(available_soldiers), 2)
            if len(available_commanders) >= 1 and len(available_soldiers) >= min_soldiers:
                self._do_assign(assign, [available_commanders[0]], schedules, 'commander')
                self._do_assign(assign, available_soldiers[:min_soldiers], schedules, 'soldier')
                self.warnings.append(f"⚠️  {assign.name}: רק {min_soldiers} חיילים")
                print(f"  ⚠️  רק {min_soldiers} חיילים")
                return True
        
        raise Exception(f"אין מספיק כוח אדם לכוננות ב ב-{assign.get_full_time_info()}")
    
    def assign_operations(self, assign: Assignment, all_people: List, schedules: Dict):
        """חמל"""
        available = [p for p in all_people 
                    if schedules[p].can_assign_at(assign.day, assign.start_hour, 
                                                  assign.length_in_hours, self.min_rest_hours)
                    and hasattr(p, 'certifications') and 'חמל' in p.certifications]
        
        if len(available) < 1:
            available = [p for p in all_people 
                        if schedules[p].can_assign_at(assign.day, assign.start_hour, 
                                                      assign.length_in_hours, self.min_rest_hours)]
        
        if len(available) >= 1:
            available.sort(key=lambda x: schedules[x].get_total_hours())
            self._do_assign(assign, [available[0]], schedules, 'soldier')
            return True
        
        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            available = [p for p in all_people 
                        if schedules[p].can_assign_at(assign.day, assign.start_hour, 
                                                      assign.length_in_hours, reduced_rest)]
            if len(available) >= 1:
                self._do_assign(assign, [available[0]], schedules, 'soldier')
                self.warnings.append(f"⚠️  {assign.name}: מנוחה מופחתת")
                return True
        
        raise Exception(f"אין מוסמך חמל זמין ב-{assign.get_full_time_info()}")
    
    def assign_kitchen(self, assign: Assignment, all_soldiers: List, schedules: Dict):
        """תורן מטבח - 24 שעות"""
        available = [s for s in all_soldiers 
                    if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                  assign.length_in_hours, self.min_rest_hours)]
        if len(available) >= 1:
            available.sort(key=lambda x: schedules[x].get_total_hours())
            self._do_assign(assign, [available[0]], schedules, 'soldier')
            print(f"    📅 משימה יומית - 24 שעות")
            return True
        
        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            available = [s for s in all_soldiers 
                        if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                      assign.length_in_hours, reduced_rest)]
            if len(available) >= 1:
                self._do_assign(assign, [available[0]], schedules, 'soldier')
                self.warnings.append(f"⚠️  {assign.name}: מנוחה מופחתת")
                return True
        
        raise Exception(f"אין חייל זמין לתורן מטבח ב-{assign.get_full_time_info()}")
    
    def assign_hafak_gashash(self, assign: Assignment, all_commanders: List, 
                            all_soldiers: List, schedules: Dict):
        """חפ״ק גשש - בעדיפות אותו אדם"""
        preferred_person = None
        if hasattr(assign, 'prefer_same_person_all_day') and assign.prefer_same_person_all_day:
            for prev_assign in schedules.values():
                for day_num, start, end, name, assign_type in prev_assign.assignments:
                    if day_num == assign.day and assign_type == AssignmentType.HAFAK_GASHASH:
                        preferred_person = prev_assign.person
                        break
                if preferred_person:
                    break
        
        if preferred_person and schedules[preferred_person].can_assign_at(
            assign.day, assign.start_hour, assign.length_in_hours, self.min_rest_hours):
            self._do_assign(assign, [preferred_person], schedules, 'soldier')
            print(f"    🎯 ממשיך מהמשמרת הקודמת")
            return True
        
        available_soldiers = [s for s in all_soldiers 
                             if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                           assign.length_in_hours, self.min_rest_hours)]
        available_commanders = [c for c in all_commanders 
                               if schedules[c].can_assign_at(assign.day, assign.start_hour, 
                                                             assign.length_in_hours, self.min_rest_hours)]
        
        all_available = available_soldiers + available_commanders
        all_available.sort(key=lambda x: schedules[x].get_total_hours())
        
        if len(all_available) >= 1:
            self._do_assign(assign, [all_available[0]], schedules, 'soldier')
            return True
        
        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            available = [p for p in (all_soldiers + all_commanders)
                        if schedules[p].can_assign_at(assign.day, assign.start_hour, 
                                                      assign.length_in_hours, reduced_rest)]
            if len(available) >= 1:
                self._do_assign(assign, [available[0]], schedules, 'soldier')
                self.warnings.append(f"⚠️  {assign.name}: מנוחה מופחתת")
                return True
        
        raise Exception(f"אין אף אחד זמין לחפ״ק גשש ב-{assign.get_full_time_info()}")
    
    def assign_shalaz(self, assign: Assignment, all_soldiers: List, schedules: Dict):
        """של״ז - 24 שעות"""
        available = [s for s in all_soldiers 
                    if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                  assign.length_in_hours, self.min_rest_hours)]
        if len(available) >= 1:
            available.sort(key=lambda x: schedules[x].get_total_hours())
            self._do_assign(assign, [available[0]], schedules, 'soldier')
            print(f"    📅 משימה יומית - 24 שעות")
            return True
        
        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            available = [s for s in all_soldiers 
                        if schedules[s].can_assign_at(assign.day, assign.start_hour, 
                                                      assign.length_in_hours, reduced_rest)]
            if len(available) >= 1:
                self._do_assign(assign, [available[0]], schedules, 'soldier')
                self.warnings.append(f"⚠️  {assign.name}: מנוחה מופחתת")
                return True
        
        raise Exception(f"אין לוחם זמין לשל״ז ב-{assign.get_full_time_info()}")
    
    def assign_duty_officer(self, assign: Assignment, all_commanders: List, schedules: Dict):
        """קצין תורן - מפקד בכיר"""
        available = [c for c in all_commanders 
                    if schedules[c].can_assign_at(assign.day, assign.start_hour, 
                                                  assign.length_in_hours, self.min_rest_hours)
                    and (c.role in ['מ"מ', 'סמל', 'מ"כ'] or 
                         (hasattr(c, 'is_platoon_commander') and c.is_platoon_commander))]
        
        if len(available) >= 1:
            available.sort(key=lambda x: schedules[x].get_total_hours())
            self._do_assign(assign, [available[0]], schedules, 'commander')
            return True
        
        if self.emergency_mode:
            available = [c for c in all_commanders 
                        if schedules[c].can_assign_at(assign.day, assign.start_hour, 
                                                      assign.length_in_hours, self.min_rest_hours)]
            if len(available) >= 1:
                self._do_assign(assign, [available[0]], schedules, 'commander')
                self.warnings.append(f"⚠️  {assign.name}: מפקד לא בכיר")
                return True
        
        raise Exception(f"אין מפקד בכיר זמין לקצין תורן ב-{assign.get_full_time_info()}")
    

    def _do_assign(self, assign: Assignment, people: List, schedules: Dict, role: str):
        """מבצע שיבוץ בפועל"""
        assigned_list = getattr(assign, f"{role}s_assigned")
        for person in people:
            assigned_list.append(person)
            schedules[person].add_assignment(
                assign.day,
                assign.start_hour,
                assign.length_in_hours,
                assign.name,
                assign.type
            )
            print(f"    • {person.name} ({person.role})")    
