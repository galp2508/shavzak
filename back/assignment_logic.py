"""
Assignment Logic - אלגוריתם השיבוץ המלא
"""
from typing import List, Dict, Tuple

class AssignmentLogic:
    """לוגיקת שיבוץ למשימות שונות - עם מצב חירום"""

    def __init__(self, min_rest_hours: int = 8, reuse_soldiers_for_standby: bool = False):
        self.min_rest_hours = min_rest_hours
        self.emergency_mode = False
        self.warnings = []
        self.reuse_soldiers_for_standby = reuse_soldiers_for_standby  # האם לאפשר שימוש חוזר בחיילים לכוננות
    
    def enable_emergency_mode(self):
        """הפעלת מצב חירום"""
        self.emergency_mode = True
    
    def can_assign_at(self, person_schedule: List[Tuple], day: int, start_hour: int,
                     length: int, min_rest: int) -> bool:
        """בודק אם אפשר לשבץ אדם"""
        end_hour = start_hour + length

        # בדיקת חפיפה
        for assign_day, assign_start, assign_end, _, _ in person_schedule:
            if assign_day == day:
                if not (end_hour <= assign_start or start_hour >= assign_end):
                    return False

        # בדיקת מנוחה
        if person_schedule:
            last_assign = max(person_schedule, key=lambda x: (x[0], x[2]))
            last_day, _, last_end, _, _ = last_assign

            if last_day == day and start_hour < last_end + min_rest:
                return False

            if last_day == day - 1:
                hours_since = (24 - last_end) + start_hour
                if hours_since < min_rest:
                    return False

        return True

    def get_recently_finished_soldiers(self, all_people: List[Dict], schedules: Dict,
                                       day: int, start_hour: int) -> List[Dict]:
        """מוצא חיילים שסיימו משימה לפני שעת ההתחלה של הכוננות.
        מיועד לכוננויות - חיילים שסיימו משימה יכולים להמשיך לכוננות."""
        recently_finished = []

        for person in all_people:
            person_id = person['id']
            if person_id not in schedules or not schedules[person_id]:
                continue

            # מצא את המשימה האחרונה של החייל ביום זה
            assignments_today = [
                (assign_start, assign_end, assign_name)
                for assign_day, assign_start, assign_end, assign_name, _ in schedules[person_id]
                if assign_day == day and assign_end <= start_hour
            ]

            if assignments_today:
                # מצא את המשימה שהסתיימה הכי קרוב לשעת ההתחלה
                last_assignment = max(assignments_today, key=lambda x: x[1])  # מקסימום לפי end_hour
                assign_start, assign_end, assign_name = last_assignment

                # אם החייל סיים משימה ממש לפני (עד 2 שעות לפני), הוא מועדף
                hours_since_finished = start_hour - assign_end
                if 0 <= hours_since_finished <= 2:
                    recently_finished.append({
                        **person,
                        'hours_since_finished': hours_since_finished,
                        'last_assignment': assign_name
                    })

        # מיין לפי מי שסיים הכי לאחרונה (פחות שעות מאז שסיים)
        recently_finished.sort(key=lambda x: x['hours_since_finished'])
        return recently_finished

    def assign_patrol(self, assign_data: Dict, mahalkot: List[Dict],
                     schedules: Dict, mahlaka_workload: Dict) -> Dict:
        """שיבוץ סיור - מפקד ולוחמים מאותה מחלקה, נהג יכול להיות מכל מחלקה"""
        result = self._try_assign_patrol_normal(assign_data, mahalkot, schedules, mahlaka_workload)
        if result:
            return result

        if self.emergency_mode:
            return self._try_assign_patrol_emergency(assign_data, mahalkot, schedules, mahlaka_workload)

        raise Exception(f"לא נמצאה מחלקה זמינה לסיור")
    
    def _try_assign_patrol_normal(self, assign_data, mahalkot, schedules, mahlaka_workload):
        """ניסיון רגיל לשיבוץ סיור - מפקד ולוחמים מאותה מחלקה, נהג מכל מחלקה"""
        # מיון לפי עומס
        mahalkot_sorted = sorted(mahalkot, key=lambda x: mahlaka_workload.get(x['id'], 0))

        # איסוף כל הנהגים הזמינים מכל המחלקות (נהג לא חייב להיות מאותה מחלקה)
        all_available_drivers = []
        for m in mahalkot:
            for d in m['drivers']:
                if self.can_assign_at(schedules.get(d['id'], []), assign_data['day'],
                                    assign_data['start_hour'], assign_data['length_in_hours'],
                                    self.min_rest_hours):
                    all_available_drivers.append(d)

        for mahlaka_info in mahalkot_sorted:
            available_commanders = [
                c for c in mahlaka_info['commanders']
                if self.can_assign_at(schedules.get(c['id'], []), assign_data['day'],
                                    assign_data['start_hour'], assign_data['length_in_hours'],
                                    self.min_rest_hours)
            ]
            available_soldiers = [
                s for s in mahlaka_info['soldiers']
                if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'],
                                    assign_data['start_hour'], assign_data['length_in_hours'],
                                    self.min_rest_hours)
            ]

            # כללי שיבוץ:
            # 1. מפקד - חובה (אם אין, לוחם יכול למלא את מקומו)
            # 2. 2 לוחמים - חובה! (אם יש רק 1, המפקד ימלא גם תפקיד לוחם)
            # 3. נהג - אופציונלי (אם אין, סיור פרוק)

            commander = None
            soldiers = []
            driver_list = []

            # חובה: מפקד + 2 לוחמים
            if available_commanders:
                commander = available_commanders[0]['id']

                # חובה: 2 לוחמים
                if len(available_soldiers) >= 2:
                    # מצוין! יש 2 לוחמים
                    soldiers = [s['id'] for s in available_soldiers[:2]]
                elif len(available_soldiers) == 1:
                    # יש רק 1 לוחם - המפקד ימלא גם תפקיד לוחם
                    soldiers = [s['id'] for s in available_soldiers[:1]]
                    self.warnings.append(f"⚠️ {assign_data['name']}: רק 1 לוחם זמין, המפקד משמש גם כלוחם")
                else:
                    # אין לוחמים בכלל - לא מספיק, עבור למחלקה הבאה
                    continue

            elif len(available_soldiers) >= 3:
                # אין מפקד אבל יש לפחות 3 לוחמים - 1 ישמש כמפקד + 2 כלוחמים
                commander = available_soldiers[0]['id']
                soldiers = [s['id'] for s in available_soldiers[1:3]]
                self.warnings.append(f"⚠️ {assign_data['name']}: לא נמצא מפקד, משובץ לוחם כמפקד")
            else:
                # לא מספיק כוח אדם במחלקה הזו
                continue

            # אם הגענו לכאן, יש מפקד + 2 לוחמים (או 1 לוחם + מפקד שמשמש גם כלוחם)
            # נהג - אופציונלי
            if all_available_drivers:
                driver_list = [all_available_drivers[0]['id']]
            else:
                # אין נהג - סיור פרוק
                self.warnings.append(f"⚠️ {assign_data['name']}: סיור פרוק - אין נהג זמין")

            return {
                'commanders': [commander],
                'drivers': driver_list,  # רשימה ריקה אם אין נהג
                'soldiers': soldiers,
                'mahlaka_id': mahlaka_info['id']
            }

        # לא נמצאה מחלקה עם מספיק כוח אדם - אסור לערבב מחלקות!
        return None

    def _try_assign_patrol_emergency(self, assign_data, mahalkot, schedules, mahlaka_workload):
        """מצב חירום - מקל על הדרישות (מנוחה מופחתת) אבל אסור לערבב מחלקות!"""
        reduced_rest = self.min_rest_hours // 2

        # איסוף כל הנהגים הזמינים עם מנוחה מופחתת (נהג יכול מכל מחלקה)
        all_available_drivers = []
        for m in mahalkot:
            for d in m['drivers']:
                if self.can_assign_at(schedules.get(d['id'], []), assign_data['day'],
                                    assign_data['start_hour'], assign_data['length_in_hours'],
                                    reduced_rest):
                    all_available_drivers.append(d)

        # נסה כל מחלקה בנפרד עם מנוחה מופחתת
        for mahlaka_info in mahalkot:
            available_commanders = [
                c for c in mahlaka_info['commanders']
                if self.can_assign_at(schedules.get(c['id'], []), assign_data['day'],
                                    assign_data['start_hour'], assign_data['length_in_hours'],
                                    reduced_rest)
            ]
            available_soldiers = [
                s for s in mahlaka_info['soldiers']
                if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'],
                                    assign_data['start_hour'], assign_data['length_in_hours'],
                                    reduced_rest)
            ]

            commander = None
            soldiers = []
            driver_list = []

            # חובה: מפקד + 2 לוחמים (גם במצב חירום!)
            if available_commanders:
                commander = available_commanders[0]['id']

                # חובה: 2 לוחמים
                if len(available_soldiers) >= 2:
                    soldiers = [s['id'] for s in available_soldiers[:2]]
                elif len(available_soldiers) == 1:
                    # יש רק 1 לוחם - המפקד ימלא גם תפקיד לוחם
                    soldiers = [s['id'] for s in available_soldiers[:1]]
                    self.warnings.append(f"⚠️ {assign_data['name']}: רק 1 לוחם זמין, המפקד משמש גם כלוחם (חירום)")
                else:
                    # אין לוחמים בכלל - עבור למחלקה הבאה
                    continue

            elif len(available_soldiers) >= 3:
                # אין מפקד אבל יש לפחות 3 לוחמים
                commander = available_soldiers[0]['id']
                soldiers = [s['id'] for s in available_soldiers[1:3]]
                self.warnings.append(f"⚠️ {assign_data['name']}: לא נמצא מפקד, משובץ לוחם כמפקד (חירום)")
            else:
                # לא מספיק כוח אדם במחלקה הזו
                continue

            # אם הגענו לכאן, יש מפקד + 2 לוחמים
            # נהג - אופציונלי
            if all_available_drivers:
                driver_list = [all_available_drivers[0]['id']]
            else:
                self.warnings.append(f"⚠️ {assign_data['name']}: סיור פרוק - אין נהג זמין")

            self.warnings.append(f"⚠️ {assign_data['name']}: מנוחה מופחתת ל-{reduced_rest} שעות")
            return {
                'commanders': [commander],
                'drivers': driver_list,
                'soldiers': soldiers,
                'mahlaka_id': mahlaka_info['id']
            }

        # לא נמצאה מחלקה עם מספיק כוח אדם גם במצב חירום
        return None
    
    def assign_guard(self, assign_data: Dict, all_soldiers: List[Dict], 
                    schedules: Dict) -> Dict:
        """שיבוץ שמירה"""
        available = [
            s for s in all_soldiers
            if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'], 
                                assign_data['start_hour'], assign_data['length_in_hours'], 
                                self.min_rest_hours)
        ]
        
        if available:
            # מיון לפי שעות עבודה (מי שעבד פחות קודם)
            available.sort(key=lambda x: sum(
                end - start for _, start, end, _, _ in schedules.get(x['id'], [])
            ))
            return {'soldiers': [available[0]['id']]}
        
        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            available = [
                s for s in all_soldiers
                if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'], 
                                    assign_data['start_hour'], assign_data['length_in_hours'], 
                                    reduced_rest)
            ]
            if available:
                self.warnings.append(f"⚠️ {assign_data['name']}: מנוחה מופחתת")
                return {'soldiers': [available[0]['id']]}
        
        raise Exception("אין חייל זמין לשמירה")
    
    def assign_standby_a(self, assign_data: Dict, all_commanders: List[Dict],
                        all_drivers: List[Dict], all_soldiers: List[Dict],
                        schedules: Dict) -> Dict:
        """שיבוץ כוננות א - מעדיף חיילים שסיימו משימה אם האופציה מופעלת"""

        # בדוק זמינות
        available_commanders = [
            c for c in all_commanders
            if self.can_assign_at(schedules.get(c['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'],
                                self.min_rest_hours)
        ]
        available_drivers = [
            d for d in all_drivers
            if self.can_assign_at(schedules.get(d['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'],
                                self.min_rest_hours)
        ]
        available_soldiers = [
            s for s in all_soldiers
            if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'],
                                self.min_rest_hours)
        ]

        if len(available_commanders) >= 1 and len(available_drivers) >= 1 and \
           len(available_soldiers) >= 7:

            # אם האופציה של שימוש חוזר מופעלת - העדף חיילים שסיימו משימה
            if self.reuse_soldiers_for_standby:
                # מצא חיילים שסיימו משימה לאחרונה
                recently_finished_commanders = self.get_recently_finished_soldiers(
                    all_commanders, schedules, assign_data['day'], assign_data['start_hour']
                )
                recently_finished_drivers = self.get_recently_finished_soldiers(
                    all_drivers, schedules, assign_data['day'], assign_data['start_hour']
                )
                recently_finished_soldiers = self.get_recently_finished_soldiers(
                    all_soldiers, schedules, assign_data['day'], assign_data['start_hour']
                )

                # העדף מפקדים שסיימו משימה לאחרונה
                available_commander_ids = {c['id'] for c in available_commanders}
                preferred_commanders = [c for c in recently_finished_commanders if c['id'] in available_commander_ids]
                if not preferred_commanders:
                    preferred_commanders = available_commanders

                # העדף נהגים שסיימו משימה לאחרונה
                available_driver_ids = {d['id'] for d in available_drivers}
                preferred_drivers = [d for d in recently_finished_drivers if d['id'] in available_driver_ids]
                if not preferred_drivers:
                    preferred_drivers = available_drivers

                # העדף לוחמים שסיימו משימה לאחרונה
                available_soldier_ids = {s['id'] for s in available_soldiers}
                preferred_soldiers = [s for s in recently_finished_soldiers if s['id'] in available_soldier_ids]

                # השלם עם לוחמים רגילים אם צריך
                remaining_needed = 7 - len(preferred_soldiers)
                if remaining_needed > 0:
                    preferred_soldier_ids = {s['id'] for s in preferred_soldiers}
                    other_soldiers = [s for s in available_soldiers if s['id'] not in preferred_soldier_ids]
                    # מיון לפי שעות עבודה (מי שעבד פחות)
                    other_soldiers.sort(key=lambda x: sum(
                        end - start for _, start, end, _, _ in schedules.get(x['id'], [])
                    ))
                    preferred_soldiers.extend(other_soldiers[:remaining_needed])
            else:
                # אופציה לא מופעלת - שיבוץ רגיל לפי שעות עבודה
                preferred_commanders = available_commanders
                preferred_drivers = available_drivers
                preferred_soldiers = available_soldiers[:7]
                # מיון לפי שעות עבודה
                preferred_soldiers.sort(key=lambda x: sum(
                    end - start for _, start, end, _, _ in schedules.get(x['id'], [])
                ))

            return {
                'commanders': [preferred_commanders[0]['id']],
                'drivers': [preferred_drivers[0]['id']],
                'soldiers': [s['id'] for s in preferred_soldiers[:7]]
            }
        
        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            available_commanders = [
                c for c in all_commanders
                if self.can_assign_at(schedules.get(c['id'], []), assign_data['day'], 
                                    assign_data['start_hour'], assign_data['length_in_hours'], 
                                    reduced_rest)
            ]
            available_drivers = [
                d for d in all_drivers
                if self.can_assign_at(schedules.get(d['id'], []), assign_data['day'], 
                                    assign_data['start_hour'], assign_data['length_in_hours'], 
                                    reduced_rest)
            ]
            available_soldiers = [
                s for s in all_soldiers
                if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'], 
                                    assign_data['start_hour'], assign_data['length_in_hours'], 
                                    reduced_rest)
            ]
            
            if len(available_commanders) >= 1 and len(available_drivers) >= 1 and \
               len(available_soldiers) >= 7:
                self.warnings.append(f"⚠️ {assign_data['name']}: מנוחה מופחתת")
                return {
                    'commanders': [available_commanders[0]['id']],
                    'drivers': [available_drivers[0]['id']],
                    'soldiers': [s['id'] for s in available_soldiers[:7]]
                }
        
        raise Exception("אין מספיק כוח אדם לכוננות א")
    
    def assign_standby_b(self, assign_data: Dict, all_commanders: List[Dict],
                        all_soldiers: List[Dict], schedules: Dict) -> Dict:
        """שיבוץ כוננות ב - מעדיף חיילים שסיימו משימה אם האופציה מופעלת"""

        # בדוק זמינות
        available_commanders = [
            c for c in all_commanders
            if self.can_assign_at(schedules.get(c['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'],
                                self.min_rest_hours)
        ]
        available_soldiers = [
            s for s in all_soldiers
            if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'],
                                self.min_rest_hours)
        ]

        if len(available_commanders) >= 1 and len(available_soldiers) >= 3:
            # אם האופציה של שימוש חוזר מופעלת - העדף חיילים שסיימו משימה
            if self.reuse_soldiers_for_standby:
                # מצא חיילים שסיימו משימה לאחרונה
                recently_finished_commanders = self.get_recently_finished_soldiers(
                    all_commanders, schedules, assign_data['day'], assign_data['start_hour']
                )
                recently_finished_soldiers = self.get_recently_finished_soldiers(
                    all_soldiers, schedules, assign_data['day'], assign_data['start_hour']
                )

                # העדף מפקדים שסיימו משימה לאחרונה
                available_commander_ids = {c['id'] for c in available_commanders}
                preferred_commanders = [c for c in recently_finished_commanders if c['id'] in available_commander_ids]
                if not preferred_commanders:
                    preferred_commanders = available_commanders

                # העדף לוחמים שסיימו משימה לאחרונה
                available_soldier_ids = {s['id'] for s in available_soldiers}
                preferred_soldiers = [s for s in recently_finished_soldiers if s['id'] in available_soldier_ids]

                # השלם עם לוחמים רגילים אם צריך
                remaining_needed = 3 - len(preferred_soldiers)
                if remaining_needed > 0:
                    preferred_soldier_ids = {s['id'] for s in preferred_soldiers}
                    other_soldiers = [s for s in available_soldiers if s['id'] not in preferred_soldier_ids]
                    # מיון לפי שעות עבודה
                    other_soldiers.sort(key=lambda x: sum(
                        end - start for _, start, end, _, _ in schedules.get(x['id'], [])
                    ))
                    preferred_soldiers.extend(other_soldiers[:remaining_needed])
            else:
                # אופציה לא מופעלת - שיבוץ רגיל לפי שעות עבודה
                preferred_commanders = available_commanders
                preferred_soldiers = available_soldiers[:3]
                # מיון לפי שעות עבודה
                preferred_soldiers.sort(key=lambda x: sum(
                    end - start for _, start, end, _, _ in schedules.get(x['id'], [])
                ))

            return {
                'commanders': [preferred_commanders[0]['id']],
                'soldiers': [s['id'] for s in preferred_soldiers[:3]]
            }
        
        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            available_commanders = [
                c for c in all_commanders
                if self.can_assign_at(schedules.get(c['id'], []), assign_data['day'], 
                                    assign_data['start_hour'], assign_data['length_in_hours'], 
                                    reduced_rest)
            ]
            available_soldiers = [
                s for s in all_soldiers
                if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'], 
                                    assign_data['start_hour'], assign_data['length_in_hours'], 
                                    reduced_rest)
            ]
            
            if len(available_commanders) >= 1 and len(available_soldiers) >= 3:
                self.warnings.append(f"⚠️ {assign_data['name']}: מנוחה מופחתת")
                return {
                    'commanders': [available_commanders[0]['id']],
                    'soldiers': [s['id'] for s in available_soldiers[:3]]
                }
        
        raise Exception("אין מספיק כוח אדם לכוננות ב")
    
    def assign_operations(self, assign_data: Dict, all_people: List[Dict], 
                         schedules: Dict) -> Dict:
        """שיבוץ חמל - דורש הסמכה"""
        certified = [
            p for p in all_people
            if 'חמל' in p.get('certifications', [])
            and self.can_assign_at(schedules.get(p['id'], []), assign_data['day'], 
                                  assign_data['start_hour'], assign_data['length_in_hours'], 
                                  self.min_rest_hours)
        ]
        
        if certified:
            return {'soldiers': [certified[0]['id']]}
        
        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            certified = [
                p for p in all_people
                if 'חמל' in p.get('certifications', [])
                and self.can_assign_at(schedules.get(p['id'], []), assign_data['day'], 
                                      assign_data['start_hour'], assign_data['length_in_hours'], 
                                      reduced_rest)
            ]
            if certified:
                self.warnings.append(f"⚠️ {assign_data['name']}: מנוחה מופחתת")
                return {'soldiers': [certified[0]['id']]}
        
        raise Exception("אין מוסמך חמל זמין")
    
    def assign_kitchen(self, assign_data: Dict, all_soldiers: List[Dict], 
                      schedules: Dict) -> Dict:
        """תורן מטבח - 24 שעות"""
        return self.assign_guard(assign_data, all_soldiers, schedules)
    
    def assign_hafak_gashash(self, assign_data: Dict, all_people: List[Dict], 
                            schedules: Dict) -> Dict:
        """חפק גשש"""
        available = [
            p for p in all_people
            if self.can_assign_at(schedules.get(p['id'], []), assign_data['day'], 
                                assign_data['start_hour'], assign_data['length_in_hours'], 
                                self.min_rest_hours)
        ]
        
        if available:
            available.sort(key=lambda x: sum(
                end - start for _, start, end, _, _ in schedules.get(x['id'], [])
            ))
            return {'soldiers': [available[0]['id']]}
        
        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            available = [
                p for p in all_people
                if self.can_assign_at(schedules.get(p['id'], []), assign_data['day'], 
                                    assign_data['start_hour'], assign_data['length_in_hours'], 
                                    reduced_rest)
            ]
            if available:
                self.warnings.append(f"⚠️ {assign_data['name']}: מנוחה מופחתת")
                return {'soldiers': [available[0]['id']]}
        
        raise Exception("אין אף אחד זמין לחפק גשש")
    
    def assign_shalaz(self, assign_data: Dict, all_soldiers: List[Dict], 
                     schedules: Dict) -> Dict:
        """של״ז - 24 שעות"""
        return self.assign_guard(assign_data, all_soldiers, schedules)
    
    def assign_duty_officer(self, assign_data: Dict, all_commanders: List[Dict], 
                           schedules: Dict) -> Dict:
        """קצין תורן - מפקד בכיר"""
        senior = [
            c for c in all_commanders
            if c['role'] in ['ממ', 'סמל', 'מכ'] or c.get('is_platoon_commander', False)
            and self.can_assign_at(schedules.get(c['id'], []), assign_data['day'], 
                                  assign_data['start_hour'], assign_data['length_in_hours'], 
                                  self.min_rest_hours)
        ]
        
        if senior:
            return {'commanders': [senior[0]['id']]}
        
        if self.emergency_mode:
            available = [
                c for c in all_commanders
                if self.can_assign_at(schedules.get(c['id'], []), assign_data['day'], 
                                    assign_data['start_hour'], assign_data['length_in_hours'], 
                                    self.min_rest_hours)
            ]
            if available:
                self.warnings.append(f"⚠️ {assign_data['name']}: מפקד לא בכיר")
                return {'commanders': [available[0]['id']]}
        
        raise Exception("אין מפקד בכיר זמין לקצין תורן")
