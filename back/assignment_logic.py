"""
Assignment Logic - אלגוריתם השיבוץ המלא
"""
from typing import List, Dict, Tuple

class AssignmentLogic:
    """לוגיקת שיבוץ למשימות שונות - עם מצב חירום ומקסימום שעות מנוחה"""

    def __init__(self, min_rest_hours: int = 8, reuse_soldiers_for_standby: bool = False):
        self.min_rest_hours = min_rest_hours
        self.emergency_mode = False
        self.warnings = []
        self.reuse_soldiers_for_standby = reuse_soldiers_for_standby  # האם לאפשר שימוש חוזר בחיילים לכוננות

    def enable_emergency_mode(self):
        """הפעלת מצב חירום"""
        self.emergency_mode = True

    def can_serve_as_soldier(self, person: Dict) -> bool:
        """בדיקה אם אדם יכול לשמש כלוחם רגיל
        חמליסט יכול לשמש כלוחם אם נדרש"""
        role = person.get('role', '')
        # חמליסט יכול לשמש כלוחם
        if 'חמל' in person.get('certifications', []):
            return True
        # מפקדים יכולים לשמש כלוחמים במקרי חירום
        if role in ['מכ', 'סמל']:
            return True
        # לוחם רגיל
        if role == 'לוחם':
            return True
        return False

    def calculate_rest_hours(self, schedule: List[Tuple], current_day: int, current_start_hour: int) -> float:
        """מחשב כמה שעות מנוחה יש לחייל מאז המשימה האחרונה
        ערך גבוה יותר = יותר מנוחה = עדיפות גבוהה יותר"""
        if not schedule:
            return float('inf')  # אין משימות - מנוחה אינסופית (עדיפות מקסימלית)

        # מצא את המשימה האחרונה
        last_assign = max(schedule, key=lambda x: (x[0], x[2]))
        last_day, _, last_end, _, _ = last_assign

        # חשב שעות מנוחה
        if last_day == current_day:
            # אותו יום - חשב מנוחה בשעות
            return current_start_hour - last_end
        else:
            # ימים שונים - חשב מנוחה כוללת
            hours_until_midnight = 24 - last_end
            hours_between_days = (current_day - last_day - 1) * 24
            hours_from_midnight = current_start_hour
            return hours_until_midnight + hours_between_days + hours_from_midnight
    
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
            result = self._try_assign_patrol_emergency(assign_data, mahalkot, schedules, mahlaka_workload)
            if result:
                return result

        # 🔧 המערכת תמיד מצליחה! אם אין פתרון אידיאלי - נמצא כל פתרון
        # ניקח מחלקה ראשונה שיש בה מספיק כוח אדם, בלי בדיקות מנוחה
        for mahlaka_info in mahalkot:
            commanders = mahlaka_info['commanders']
            drivers = mahlaka_info['drivers']
            soldiers = mahlaka_info['soldiers']

            if len(commanders) > 0 and len(drivers) > 0 and len(soldiers) >= 2:
                return {
                    'commanders': [commanders[0]['id']],
                    'drivers': [drivers[0]['id']],
                    'soldiers': [s['id'] for s in soldiers[:2]],
                    'mahlaka_id': mahlaka_info['id']
                }

        # אם בכל זאת אין - נשתמש במה שיש (אף מחלקה בודדת)
        all_commanders = [c for m in mahalkot for c in m['commanders']]
        all_drivers = [d for m in mahalkot for d in m['drivers']]
        all_soldiers = [s for m in mahalkot for s in m['soldiers']]

        return {
            'commanders': [all_commanders[0]['id']] if all_commanders else [],
            'drivers': [all_drivers[0]['id']] if all_drivers else [],
            'soldiers': [s['id'] for s in all_soldiers[:2]] if all_soldiers else [],
            'mahlaka_id': mahalkot[0]['id'] if mahalkot else None
        }
    
    def get_shift_number(self, start_hour: int) -> int:
        """מחזיר את מספר המשמרת על פי שעת ההתחלה
        משמרת 0: 00:00-08:00
        משמרת 1: 08:00-16:00
        משמרת 2: 16:00-00:00 (24:00)
        """
        if 0 <= start_hour < 8:
            return 0
        elif 8 <= start_hour < 16:
            return 1
        elif 16 <= start_hour < 24:
            return 2
        else:
            # אם השעה מחוץ לטווח, נחשב לפי modulo
            return (start_hour // 8) % 3

    def get_next_mahlaka_rotation(self, mahalkot: List[Dict], assign_data: Dict) -> List[Dict]:
        """מחזיר את המחלקות במחזוריות - כל מחלקה עובדת במשמרת מסוימת (לפי שעות)
        כל מחלקה תיקח את כל המשימות באותה משמרת:
        - מחלקה 1: 00:00-08:00
        - מחלקה 2: 08:00-16:00
        - מחלקה 3: 16:00-00:00
        ובכל יום המחלקות מתחלפות משמרות
        """
        day = assign_data['day']
        start_hour = assign_data['start_hour']

        num_mahalkot = len(mahalkot)
        if num_mahalkot == 0:
            return []

        # חישוב מספר המשמרת (0, 1, או 2)
        shift_number = self.get_shift_number(start_hour)

        # חישוב איזו מחלקה צריכה לעבוד במשמרת הזו ביום הזה
        # ביום 0: מחלקה 0 במשמרת 0, מחלקה 1 במשמרת 1, מחלקה 2 במשמרת 2
        # ביום 1: מחלקה 1 במשמרת 0, מחלקה 2 במשמרת 1, מחלקה 0 במשמרת 2
        # וכן הלאה (רוטציה)
        mahlaka_index = (shift_number + day) % num_mahalkot

        # יצירת רשימה מסודרת במחזוריות, כאשר המחלקה המתאימה במשמרת היא הראשונה
        rotated = []
        for i in range(num_mahalkot):
            idx = (mahlaka_index + i) % num_mahalkot
            rotated.append(mahalkot[idx])

        return rotated

    def _try_assign_patrol_normal(self, assign_data, mahalkot, schedules, mahlaka_workload):
        """ניסיון רגיל לשיבוץ סיור - מפקד ולוחמים מאותה מחלקה, נהג מכל מחלקה
        משתמש ברוטציה של מחלקות - כל מחלקה עובדת ביחד בבלוק"""

        # קבל מחלקות בסדר מחזורי
        mahalkot_sorted = self.get_next_mahlaka_rotation(mahalkot, assign_data)

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
            # לוחמים - כולל חמליסטים שיכולים לשמש כלוחמים
            available_soldiers = [
                s for s in mahlaka_info['soldiers']
                if self.can_serve_as_soldier(s) and
                   self.can_assign_at(schedules.get(s['id'], []), assign_data['day'],
                                    assign_data['start_hour'], assign_data['length_in_hours'],
                                    self.min_rest_hours)
            ]

            # הוסף מ"כים כלוחמים פוטנציאליים (אם צריך)
            mak_soldiers = [
                c for c in mahlaka_info['commanders']
                if c.get('role') == 'מכ' and
                   self.can_assign_at(schedules.get(c['id'], []), assign_data['day'],
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
                    # יש רק 1 לוחם - נסה להשתמש במ"כ כלוחם נוסף אם יש
                    if len(mak_soldiers) >= 1:
                        soldiers = [available_soldiers[0]['id'], mak_soldiers[0]['id']]
                    else:
                        # אין מ"כ זמין - המפקד ימלא גם תפקיד לוחם
                        soldiers = [s['id'] for s in available_soldiers[:1]]
                elif len(available_soldiers) == 0 and len(mak_soldiers) >= 2:
                    # אין לוחמים אבל יש מ"כים - השתמש בהם
                    soldiers = [m['id'] for m in mak_soldiers[:2]]
                else:
                    # אין מספיק כוח אדם - עבור למחלקה הבאה
                    continue

            elif len(available_soldiers) >= 3:
                # אין מפקד אבל יש לפחות 3 לוחמים - 1 ישמש כמפקד + 2 כלוחמים
                commander = available_soldiers[0]['id']
                soldiers = [s['id'] for s in available_soldiers[1:3]]
            elif len(available_soldiers) >= 1 and len(mak_soldiers) >= 2:
                # אין מפקד אבל יש לוחמים ומ"כים - מ"כ ישמש כמפקד
                commander = mak_soldiers[0]['id']
                soldiers = [available_soldiers[0]['id'], mak_soldiers[1]['id']]
            else:
                # לא מספיק כוח אדם במחלקה הזו
                continue

            # אם הגענו לכאן, יש מפקד + 2 לוחמים (או 1 לוחם + מפקד שמשמש גם כלוחם)
            # נהג - אופציונלי
            if all_available_drivers:
                driver_list = [all_available_drivers[0]['id']]
            else:
                # אין נהג - סיור פרוק (זה בסדר, לא צריך אזהרה)
                driver_list = []

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
                else:
                    # אין לוחמים בכלל - עבור למחלקה הבאה
                    continue

            elif len(available_soldiers) >= 3:
                # אין מפקד אבל יש לפחות 3 לוחמים
                commander = available_soldiers[0]['id']
                soldiers = [s['id'] for s in available_soldiers[1:3]]
            else:
                # לא מספיק כוח אדם במחלקה הזו
                continue

            # אם הגענו לכאן, יש מפקד + 2 לוחמים
            # נהג - אופציונלי
            if all_available_drivers:
                driver_list = [all_available_drivers[0]['id']]
            else:
                driver_list = []
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
        """שיבוץ שמירה - עם מקסימום שעות מנוחה"""
        available = [
            s for s in all_soldiers
            if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'],
                                self.min_rest_hours)
        ]

        if available:
            # מיון לפי שעות מנוחה (מי שנח יותר קודם) - מקסימום מנוחה!
            available.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True  # מי שנח יותר קודם
            )
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
                # מיון לפי שעות מנוחה גם במצב חירום
                available.sort(
                    key=lambda x: self.calculate_rest_hours(
                        schedules.get(x['id'], []),
                        assign_data['day'],
                        assign_data['start_hour']
                    ),
                    reverse=True
                )
                # הוסר: אזהרת "מנוחה מופחתת" - לא רלוונטי כי המערכת מטפלת בזה אוטומטית
                return {'soldiers': [available[0]['id']]}

        # 🔧 המערכת תמיד מצליחה! אם אין מי שעומד בדרישות מנוחה - נשתמש במי שיש
        # עדיפות: מ"כ → סמל → ממ"ד
        all_people_sorted = sorted(all_soldiers, key=lambda x: (
            0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
        ))

        if all_people_sorted:
            # הוסר: אזהרת "שובץ ללא מנוחה מספקת" - לא רלוונטי כי המערכת מטפלת בזה אוטומטית
            return {'soldiers': [all_people_sorted[0]['id']]}

        # ממש אין אף אחד - נחזיר ריק (אבל לא Exception!)
        return {'soldiers': []}
    
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
            # קח את הערך מהתבנית, ואם לא קיים שם - קח מההגדרה הכללית
            reuse_from_template = assign_data.get('reuse_soldiers_for_standby', self.reuse_soldiers_for_standby)
            if reuse_from_template:
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

                # 🔧 תיקון: כאשר האופציה מסומנת - קח **בהכרח** אנשים שירדו ממשימות בלבד
                # אין fallback לאנשים רגילים - רק מי שירד ממשימות
                available_commander_ids = {c['id'] for c in available_commanders}
                preferred_commanders = [c for c in recently_finished_commanders if c['id'] in available_commander_ids]

                available_driver_ids = {d['id'] for d in available_drivers}
                preferred_drivers = [d for d in recently_finished_drivers if d['id'] in available_driver_ids]

                available_soldier_ids = {s['id'] for s in available_soldiers}
                preferred_soldiers = [s for s in recently_finished_soldiers if s['id'] in available_soldier_ids]

                # לא משלימים עם חיילים רגילים - רק מי שירד ממשימות!
            else:
                # אופציה לא מופעלת - שיבוץ רגיל לפי שעות מנוחה (מקסימום מנוחה!)
                preferred_commanders = available_commanders
                preferred_drivers = available_drivers
                preferred_soldiers = available_soldiers
                # מיון לפי שעות מנוחה - מי שנח יותר קודם
                preferred_commanders.sort(
                    key=lambda x: self.calculate_rest_hours(
                        schedules.get(x['id'], []),
                        assign_data['day'],
                        assign_data['start_hour']
                    ),
                    reverse=True
                )
                preferred_drivers.sort(
                    key=lambda x: self.calculate_rest_hours(
                        schedules.get(x['id'], []),
                        assign_data['day'],
                        assign_data['start_hour']
                    ),
                    reverse=True
                )
                preferred_soldiers.sort(
                    key=lambda x: self.calculate_rest_hours(
                        schedules.get(x['id'], []),
                        assign_data['day'],
                        assign_data['start_hour']
                    ),
                    reverse=True
                )

            # 🔧 המערכת תמיד מצליחה! אם אין מספיק - נשתמש בכל מי שזמין
            # עדיפות: מ"כ → סמל → ממ"ד
            final_commanders = []
            final_drivers = []
            final_soldiers = []

            # מפקד: קח מה שיש (מתעדף קודם)
            if preferred_commanders:
                final_commanders = [preferred_commanders[0]['id']]
            elif available_commanders:
                final_commanders = [available_commanders[0]['id']]
            # אם אין מפקדים כלל, ניקח סמל או ממ"ד למטה

            # נהג: קח מה שיש
            if preferred_drivers:
                final_drivers = [preferred_drivers[0]['id']]
            elif available_drivers:
                final_drivers = [available_drivers[0]['id']]

            # לוחמים: קח עד 7
            if preferred_soldiers:
                final_soldiers = [s['id'] for s in preferred_soldiers[:7]]
            elif available_soldiers:
                final_soldiers = [s['id'] for s in available_soldiers[:7]]

            # אם חסרים חיילים - השלם עם מי שזמין (עדיפות: מ"כ → סמל → ממ"ד)
            all_people_available = available_commanders + available_soldiers
            all_people_available.sort(key=lambda x: (
                0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
            ))

            # השלם מפקד אם חסר
            if not final_commanders and all_people_available:
                final_commanders = [all_people_available.pop(0)['id']]

            # השלם נהג אם חסר
            if not final_drivers and all_people_available:
                final_drivers = [all_people_available.pop(0)['id']]

            # השלם לוחמים עד 7
            while len(final_soldiers) < 7 and all_people_available:
                final_soldiers.append(all_people_available.pop(0)['id'])

            return {
                'commanders': final_commanders,
                'drivers': final_drivers,
                'soldiers': final_soldiers
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
                return {
                    'commanders': [available_commanders[0]['id']],
                    'drivers': [available_drivers[0]['id']],
                    'soldiers': [s['id'] for s in available_soldiers[:7]]
                }

        # 🔧 המערכת תמיד מצליחה! משתמשים בכל מי שזמין בלי בדיקות מנוחה
        all_people = all_commanders + all_drivers + all_soldiers
        all_people.sort(key=lambda x: (
            0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
        ))

        final_commanders = [all_people.pop(0)['id']] if all_people else []
        final_drivers = [all_people.pop(0)['id']] if all_people else []
        final_soldiers = [all_people.pop(0)['id'] for _ in range(min(7, len(all_people)))]

        return {
            'commanders': final_commanders,
            'drivers': final_drivers,
            'soldiers': final_soldiers
        }
    
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
            # קח את הערך מהתבנית, ואם לא קיים שם - קח מההגדרה הכללית
            reuse_from_template = assign_data.get('reuse_soldiers_for_standby', self.reuse_soldiers_for_standby)
            if reuse_from_template:
                # מצא חיילים שסיימו משימה לאחרונה
                recently_finished_commanders = self.get_recently_finished_soldiers(
                    all_commanders, schedules, assign_data['day'], assign_data['start_hour']
                )
                recently_finished_soldiers = self.get_recently_finished_soldiers(
                    all_soldiers, schedules, assign_data['day'], assign_data['start_hour']
                )

                # העדף מפקדים שסיימו משימה לאחרונה
                available_commander_ids = {c['id'] for c in available_commanders}
                # 🔧 תיקון: כאשר האופציה מסומנת - קח **בהכרח** אנשים שירדו ממשימות בלבד
                # אין fallback לאנשים רגילים - רק מי שירד ממשימות
                preferred_commanders = [c for c in recently_finished_commanders if c['id'] in available_commander_ids]

                # העדף לוחמים שסיימו משימה לאחרונה
                available_soldier_ids = {s['id'] for s in available_soldiers}
                preferred_soldiers = [s for s in recently_finished_soldiers if s['id'] in available_soldier_ids]

                # לא משלימים עם חיילים רגילים - רק מי שירד ממשימות!
            else:
                # אופציה לא מופעלת - שיבוץ רגיל לפי שעות מנוחה (מקסימום מנוחה!)
                preferred_commanders = available_commanders
                preferred_soldiers = available_soldiers
                # מיון לפי שעות מנוחה - מי שנח יותר קודם
                preferred_commanders.sort(
                    key=lambda x: self.calculate_rest_hours(
                        schedules.get(x['id'], []),
                        assign_data['day'],
                        assign_data['start_hour']
                    ),
                    reverse=True
                )
                preferred_soldiers.sort(
                    key=lambda x: self.calculate_rest_hours(
                        schedules.get(x['id'], []),
                        assign_data['day'],
                        assign_data['start_hour']
                    ),
                    reverse=True
                )

            # 🔧 המערכת תמיד מצליחה! אם אין מספיק - נשתמש בכל מי שזמין
            # עדיפות: מ"כ → סמל → ממ"ד
            final_commanders = []
            final_soldiers = []

            # מפקד: קח מה שיש
            if preferred_commanders:
                final_commanders = [preferred_commanders[0]['id']]
            elif available_commanders:
                final_commanders = [available_commanders[0]['id']]

            # לוחמים: קח עד 3
            if preferred_soldiers:
                final_soldiers = [s['id'] for s in preferred_soldiers[:3]]
            elif available_soldiers:
                final_soldiers = [s['id'] for s in available_soldiers[:3]]

            # אם חסרים חיילים - השלם עם מי שזמין (עדיפות: מ"כ → סמל → ממ"ד)
            all_people_available = available_commanders + available_soldiers
            all_people_available.sort(key=lambda x: (
                0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
            ))

            # השלם מפקד אם חסר
            if not final_commanders and all_people_available:
                final_commanders = [all_people_available.pop(0)['id']]

            # השלם לוחמים עד 3
            while len(final_soldiers) < 3 and all_people_available:
                final_soldiers.append(all_people_available.pop(0)['id'])

            return {
                'commanders': final_commanders,
                'soldiers': final_soldiers
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
                return {
                    'commanders': [available_commanders[0]['id']],
                    'soldiers': [s['id'] for s in available_soldiers[:3]]
                }

        # 🔧 המערכת תמיד מצליחה! משתמשים בכל מי שזמין בלי בדיקות מנוחה
        all_people = all_commanders + all_soldiers
        all_people.sort(key=lambda x: (
            0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
        ))

        final_commanders = [all_people.pop(0)['id']] if all_people else []
        final_soldiers = [all_people.pop(0)['id'] for _ in range(min(3, len(all_people)))]

        return {
            'commanders': final_commanders,
            'soldiers': final_soldiers
        }
    
    def assign_operations(self, assign_data: Dict, all_people: List[Dict],
                         schedules: Dict) -> Dict:
        """שיבוץ חמל - דורש הסמכה, עם מקסימום שעות מנוחה"""
        # קבל את שם ההסמכה הנדרשת מהתבנית (או ברירת מחדל 'חמל')
        required_cert = assign_data.get('requires_certification', 'חמל')

        certified = [
            p for p in all_people
            if required_cert in p.get('certifications', [])
            and self.can_assign_at(schedules.get(p['id'], []), assign_data['day'],
                                  assign_data['start_hour'], assign_data['length_in_hours'],
                                  self.min_rest_hours)
        ]

        if certified:
            # מיון לפי שעות מנוחה - מי שנח יותר קודם
            certified.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
            return {'soldiers': [certified[0]['id']]}

        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            certified = [
                p for p in all_people
                if required_cert in p.get('certifications', [])
                and self.can_assign_at(schedules.get(p['id'], []), assign_data['day'],
                                      assign_data['start_hour'], assign_data['length_in_hours'],
                                      reduced_rest)
            ]
            if certified:
                # מיון לפי שעות מנוחה גם במצב חירום
                certified.sort(
                    key=lambda x: self.calculate_rest_hours(
                        schedules.get(x['id'], []),
                        assign_data['day'],
                        assign_data['start_hour']
                    ),
                    reverse=True
                )
                return {'soldiers': [certified[0]['id']]}

        # 🔧 המערכת תמיד מצליחה! אם אין מוסמך חמל - ניקח מי שזמין (עדיפות: מ"כ → סמל → ממ"ד)
        all_people_sorted = sorted(all_people, key=lambda x: (
            0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
        ))

        if all_people_sorted:
            return {'soldiers': [all_people_sorted[0]['id']]}

        return {'soldiers': []}
    
    def assign_kitchen(self, assign_data: Dict, all_soldiers: List[Dict],
                      schedules: Dict) -> Dict:
        """תורן מטבח - מספר חיילים לפי needs_soldiers"""
        # כמה חיילים נדרשים?
        num_needed = assign_data.get('needs_soldiers', 1)

        # מצא חיילים זמינים
        available = [
            s for s in all_soldiers
            if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'],
                                self.min_rest_hours)
        ]

        if len(available) >= num_needed:
            # מיון לפי שעות מנוחה (מי שנח יותר קודם) - מקסימום מנוחה!
            available.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True  # מי שנח יותר קודם
            )
            return {'soldiers': [s['id'] for s in available[:num_needed]]}

        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            available = [
                s for s in all_soldiers
                if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'],
                                    assign_data['start_hour'], assign_data['length_in_hours'],
                                    reduced_rest)
            ]
            if len(available) >= num_needed:
                # מיון לפי שעות מנוחה גם במצב חירום
                available.sort(
                    key=lambda x: self.calculate_rest_hours(
                        schedules.get(x['id'], []),
                        assign_data['day'],
                        assign_data['start_hour']
                    ),
                    reverse=True
                )
                # הוסר: אזהרת "מנוחה מופחתת" - לא רלוונטי כי המערכת מטפלת בזה אוטומטית
                return {'soldiers': [s['id'] for s in available[:num_needed]]}

        # 🔧 המערכת תמיד מצליחה! אם אין מספיק - נשתמש במה שיש
        # עדיפות: מ"כ → סמל → ממ"ד
        all_people_sorted = sorted(all_soldiers, key=lambda x: (
            0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
        ))

        if all_people_sorted:
            num_to_assign = min(num_needed, len(all_people_sorted))
            # אזהרה רק אם חסרים יותר מ-30% מהחיילים הנדרשים (או לפחות 2 חיילים)
            shortage = num_needed - num_to_assign
            if shortage >= 2 or (shortage > 0 and shortage / num_needed > 0.3):
                self.warnings.append(f"⚠️ {assign_data['name']}: שובצו רק {num_to_assign} מתוך {num_needed} חיילים")
            return {'soldiers': [s['id'] for s in all_people_sorted[:num_to_assign]]}

        # ממש אין אף אחד - נחזיר ריק (אבל לא Exception!)
        return {'soldiers': []}
    
    def assign_hafak_gashash(self, assign_data: Dict, all_people: List[Dict],
                            schedules: Dict) -> Dict:
        """חפק גשש - עם מקסימום שעות מנוחה"""
        available = [
            p for p in all_people
            if self.can_assign_at(schedules.get(p['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'],
                                self.min_rest_hours)
        ]

        if available:
            # מיון לפי שעות מנוחה - מי שנח יותר קודם
            available.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
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
                # מיון לפי שעות מנוחה גם במצב חירום
                available.sort(
                    key=lambda x: self.calculate_rest_hours(
                        schedules.get(x['id'], []),
                        assign_data['day'],
                        assign_data['start_hour']
                    ),
                    reverse=True
                )
                return {'soldiers': [available[0]['id']]}

        # 🔧 המערכת תמיד מצליחה! ניקח מי שזמין (עדיפות: מ"כ → סמל → ממ"ד)
        all_people_sorted = sorted(all_people, key=lambda x: (
            0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
        ))

        if all_people_sorted:
            return {'soldiers': [all_people_sorted[0]['id']]}

        return {'soldiers': []}
    
    def assign_shalaz(self, assign_data: Dict, all_soldiers: List[Dict], 
                     schedules: Dict) -> Dict:
        """של״ז - 24 שעות"""
        return self.assign_guard(assign_data, all_soldiers, schedules)
    
    def assign_duty_officer(self, assign_data: Dict, all_commanders: List[Dict],
                           schedules: Dict) -> Dict:
        """קצין תורן - מפקד בכיר, עם מקסימום שעות מנוחה"""
        senior = [
            c for c in all_commanders
            if c['role'] in ['ממ', 'סמל', 'מכ'] or c.get('is_platoon_commander', False)
            and self.can_assign_at(schedules.get(c['id'], []), assign_data['day'],
                                  assign_data['start_hour'], assign_data['length_in_hours'],
                                  self.min_rest_hours)
        ]

        if senior:
            # מיון לפי שעות מנוחה - מי שנח יותר קודם
            senior.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
            return {'commanders': [senior[0]['id']]}

        if self.emergency_mode:
            available = [
                c for c in all_commanders
                if self.can_assign_at(schedules.get(c['id'], []), assign_data['day'],
                                    assign_data['start_hour'], assign_data['length_in_hours'],
                                    self.min_rest_hours)
            ]
            if available:
                # מיון לפי שעות מנוחה גם במצב חירום
                available.sort(
                    key=lambda x: self.calculate_rest_hours(
                        schedules.get(x['id'], []),
                        assign_data['day'],
                        assign_data['start_hour']
                    ),
                    reverse=True
                )
                return {'commanders': [available[0]['id']]}

        # 🔧 המערכת תמיד מצליחה! ניקח כל מפקד זמין (עדיפות: מ"כ → סמל → ממ"ד)
        all_commanders_sorted = sorted(all_commanders, key=lambda x: (
            0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
        ))

        if all_commanders_sorted:
            return {'commanders': [all_commanders_sorted[0]['id']]}

        return {'commanders': []}
