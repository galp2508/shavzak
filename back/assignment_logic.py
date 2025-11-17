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
        """מוצא חיילים שסיימו משימה ממש לפני שעת ההתחלה של הכוננות.
        מיועד לכוננויות - חיילים שסיימו משימה יכולים להמשיך לכוננות מיד."""
        recently_finished = []

        for person in all_people:
            person_id = person['id']
            if person_id not in schedules or not schedules[person_id]:
                continue

            # מצא את המשימה האחרונה של החייל בכל הימים עד עכשיו
            all_assignments = [
                (assign_day, assign_start, assign_end, assign_name)
                for assign_day, assign_start, assign_end, assign_name, _ in schedules[person_id]
            ]

            if all_assignments:
                # מצא את המשימה שהסתיימה הכי לאחרונה (לפי יום ושעה)
                last_assignment = max(all_assignments, key=lambda x: (x[0], x[2]))  # (day, end_hour)
                assign_day, assign_start, assign_end, assign_name = last_assignment

                # חשב כמה שעות עברו מאז סיום המשימה
                if assign_day == day:
                    # אותו יום
                    hours_since = start_hour - assign_end
                elif assign_day == day - 1:
                    # יום קודם
                    hours_since = (24 - assign_end) + start_hour
                else:
                    # יותר מיום
                    hours_since = ((day - assign_day - 1) * 24) + (24 - assign_end) + start_hour

                # רק אם המשימה הסתיימה ממש לפני (עד 1 שעה)
                # זה מבטיח שהחייל ירד ממשימה ומיד ממשיך לכוננות
                if 0 <= hours_since <= 1:
                    recently_finished.append({
                        **person,
                        'hours_since_finished': hours_since,
                        'last_assignment': assign_name
                    })

        # מיין לפי מי שסיים הכי לאחרונה (פחות שעות מאז שסיים)
        recently_finished.sort(key=lambda x: x['hours_since_finished'])
        return recently_finished

    def get_recently_finished_tasks_by_type(self, all_people: List[Dict], schedules: Dict,
                                           day: int, start_hour: int, task_types: List[str]) -> List[Dict]:
        """מוצא משימות שהסתיימו לאחרונה לפי סוגים (סיור, שמירה וכו')
        מחזיר רשימה של משימות עם כל האנשים שהשתתפו בהן

        Args:
            all_people: כל האנשים (מפקדים + נהגים + לוחמים)
            schedules: לוח זמנים של כולם
            day: היום הנוכחי
            start_hour: שעת ההתחלה של הכוננות
            task_types: סוגי משימות לחפש (למשל ['סיור'] או ['שמירה'])

        Returns:
            רשימה של משימות ממוינות לפי זמן סיום (האחרונות קודם)
            כל משימה מכילה: name, type, day, start, end, hours_since, participants
        """
        finished_tasks = {}  # (name, day, start, end, type) -> task_info

        for person in all_people:
            person_id = person['id']
            if person_id not in schedules or not schedules[person_id]:
                continue

            for assign_day, assign_start, assign_end, assign_name, assign_type in schedules[person_id]:
                if assign_type not in task_types:
                    continue

                # חשב כמה שעות עברו מאז סיום המשימה
                if assign_day == day:
                    hours_since = start_hour - assign_end
                elif assign_day == day - 1:
                    hours_since = (24 - assign_end) + start_hour
                else:
                    hours_since = ((day - assign_day - 1) * 24) + (24 - assign_end) + start_hour

                # רק אם המשימה הסתיימה ממש לפני (עד 1 שעה)
                if 0 <= hours_since <= 1:
                    task_key = (assign_name, assign_day, assign_start, assign_end, assign_type)
                    if task_key not in finished_tasks:
                        finished_tasks[task_key] = {
                            'name': assign_name,
                            'type': assign_type,
                            'day': assign_day,
                            'start': assign_start,
                            'end': assign_end,
                            'hours_since': hours_since,
                            'participants': []
                        }

                    # הוסף את האדם למשימה (אם הוא עדיין לא שם)
                    if person not in finished_tasks[task_key]['participants']:
                        finished_tasks[task_key]['participants'].append(person)

        # מיין לפי מי שסיים הכי לאחרונה (פחות שעות מאז שסיים)
        return sorted(finished_tasks.values(), key=lambda x: x['hours_since'])

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

    def get_next_mahlaka_rotation(self, mahalkot: List[Dict], assign_data: Dict, mahlaka_workload: Dict = None) -> List[Dict]:
        """מחזיר את המחלקות לפי עומס עבודה - מחלקות שעבדו פחות קודמות
        אם אין נתוני עומס, משתמש ברוטציה מכנית לפי יום ומשמרת
        """
        num_mahalkot = len(mahalkot)
        if num_mahalkot == 0:
            return []

        # אם יש נתוני עומס, מיין לפי העומס (מי שעבד פחות קודם)
        if mahlaka_workload is not None:
            sorted_mahalkot = sorted(
                mahalkot,
                key=lambda m: mahlaka_workload.get(m['id'], 0)
            )
            return sorted_mahalkot

        # אחרת, רוטציה מכנית (גיבוי)
        day = assign_data['day']
        start_hour = assign_data['start_hour']
        shift_number = self.get_shift_number(start_hour)
        mahlaka_index = (shift_number + day) % num_mahalkot

        rotated = []
        for i in range(num_mahalkot):
            idx = (mahlaka_index + i) % num_mahalkot
            rotated.append(mahalkot[idx])

        return rotated

    def _try_assign_patrol_normal(self, assign_data, mahalkot, schedules, mahlaka_workload):
        """ניסיון רגיל לשיבוץ סיור - מפקד ולוחמים מאותה מחלקה, נהג מכל מחלקה
        משתמש ברוטציה של מחלקות - כל מחלקה עובדת ביחד בבלוק"""

        # קבל מחלקות בסדר לפי עומס (מי שעבד פחות קודם)
        mahalkot_sorted = self.get_next_mahlaka_rotation(mahalkot, assign_data, mahlaka_workload)

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

            # עדכון עומס המחלקה
            if mahlaka_workload is not None:
                mahlaka_workload[mahlaka_info['id']] = mahlaka_workload.get(mahlaka_info['id'], 0) + assign_data['length_in_hours']

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

            # עדכון עומס המחלקה
            if mahlaka_workload is not None:
                mahlaka_workload[mahlaka_info['id']] = mahlaka_workload.get(mahlaka_info['id'], 0) + assign_data['length_in_hours']

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
        """שיבוץ שמירה - עם מקסימום שעות מנוחה + מחלקה"""
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
            selected_soldier = available[0]
            return {
                'soldiers': [selected_soldier['id']],
                'mahlaka_id': selected_soldier.get('mahlaka_id')  # שמירת מחלקה
            }

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

        # 🔧 המערכת תמיד מצליחה! אם אין מי שעומד בדרישות מנוחה - נשתמש במי שזמין
        # אבל עדיין צריך לבדוק שהוא לא משובץ באותו זמן!
        available_people = [
            s for s in all_soldiers
            if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'],
                                 assign_data['start_hour'], assign_data['length_in_hours'],
                                 0)  # אפס מנוחה - רק בדיקת חפיפה
        ]

        if available_people:
            # עדיפות: מי שנח הכי הרבה
            available_people.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
            return {'soldiers': [available_people[0]['id']]}

        # ממש אין אף אחד - נחזיר ריק (אבל לא Exception!)
        return {'soldiers': []}
    
    def _try_build_standby_a_from_patrols(self, assign_data: Dict, all_commanders: List[Dict],
                                          all_drivers: List[Dict], all_soldiers: List[Dict],
                                          schedules: Dict) -> Dict:
        """ניסיון לבנות כוננות א' מ-2 סיורים שהסתיימו

        לוקח:
        - 6 לוחמים מ-2 הסיורים האחרונים (לא נהגים!)
        - מפקדים מהסיורים
        - המפקד הבכיר = מפקד הככ"א
        - נהג זמין (לא מהסיורים - כי נהגים צריכים 16 שעות מנוחה)

        Returns:
            Dict עם commanders, drivers, soldiers או None אם לא הצליח
        """
        # מצא סיורים שהסתיימו
        all_people = all_commanders + all_drivers + all_soldiers
        finished_patrols = self.get_recently_finished_tasks_by_type(
            all_people, schedules, assign_data['day'], assign_data['start_hour'], ['סיור']
        )

        # צריך לפחות 2 סיורים
        if len(finished_patrols) < 2:
            return None

        # קח את 2 הסיורים הראשונים (האחרונים שהסתיימו)
        patrol1 = finished_patrols[0]
        patrol2 = finished_patrols[1]

        # הפרד לוחמים ומפקדים מהסיורים (ללא נהגים!)
        commanders_from_patrols = []
        soldiers_from_patrols = []

        for patrol in [patrol1, patrol2]:
            for participant in patrol['participants']:
                # סנן נהגים - הם לא צריכים להיכלל!
                if 'נהג' in participant.get('certifications', []):
                    continue

                # הפרד מפקדים מלוחמים
                if participant['role'] in ['מכ', 'ממ', 'סמל']:
                    commanders_from_patrols.append(participant)
                else:
                    soldiers_from_patrols.append(participant)

        # מצא מפקד בכיר - רק מכ או ממ (לא סמל!)
        # עדיפות: 1. מכ (מפקד מחלקה), 2. ממ
        senior_commander = None

        # קודם כולם - מכ (מפקד מחלקה)
        for cmd in commanders_from_patrols:
            if cmd['role'] == 'מכ':
                senior_commander = cmd
                break

        # אם אין מכ, קח ממ
        if not senior_commander:
            for cmd in commanders_from_patrols:
                if cmd['role'] == 'ממ':
                    senior_commander = cmd
                    break

        # בדוק שיש מספיק לוחמים (צריך 7)
        if len(soldiers_from_patrols) < 7:
            return None

        # בדוק שיש מפקד
        if not senior_commander:
            return None

        # מצא נהג זמין (לא מהסיורים!)
        # נהגים צריכים 16 שעות מנוחה אם הם עושים משימות נהיגה
        available_drivers = [
            d for d in all_drivers
            if self.can_assign_at(schedules.get(d['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'],
                                self.min_rest_hours)
        ]

        if not available_drivers:
            return None

        # בדוק שהמפקד והלוחמים זמינים לכוננות (לא משובצים)
        if not self.can_assign_at(schedules.get(senior_commander['id'], []), assign_data['day'],
                                 assign_data['start_hour'], assign_data['length_in_hours'], 0):
            return None

        final_soldiers = []
        for soldier in soldiers_from_patrols[:7]:
            if self.can_assign_at(schedules.get(soldier['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'], 0):
                final_soldiers.append(soldier['id'])

        # בדוק שיש לפחות 7 לוחמים זמינים
        if len(final_soldiers) < 7:
            return None

        return {
            'commanders': [senior_commander['id']],
            'drivers': [available_drivers[0]['id']],
            'soldiers': final_soldiers[:7]
        }

    def assign_standby_a(self, assign_data: Dict, all_commanders: List[Dict],
                        all_drivers: List[Dict], all_soldiers: List[Dict],
                        schedules: Dict) -> Dict:
        """שיבוץ כוננות א - לוקח אנשים מ-2 סיורים אחרונים אם האופציה מופעלת"""

        # קח את הערך מהתבנית, ואם לא קיים שם - קח מההגדרה הכללית
        reuse_from_template = assign_data.get('reuse_soldiers_for_standby', self.reuse_soldiers_for_standby)

        if reuse_from_template:
            # נסה לבנות כוננות מ-2 סיורים שהסתיימו
            result = self._try_build_standby_a_from_patrols(
                assign_data, all_commanders, all_drivers, all_soldiers, schedules
            )
            if result:
                # כוננות א' תמיד פלוגתית (לוקחת אנשים ממחלקות שונות)
                result['mahlaka_id'] = 'pluga'
                return result
            # אם לא הצלחנו לבנות מסיורים - לא משלימים! החזר ריק
            return {'commanders': [], 'drivers': [], 'soldiers': [], 'mahlaka_id': 'pluga'}

        # שיבוץ רגיל - לא מסומן reuse
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
            # מיון לפי שעות מנוחה - מי שנח יותר קודם
            available_commanders.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
            available_drivers.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
            available_soldiers.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )

            # כוננות א' תמיד פלוגתית
            return {
                'commanders': [available_commanders[0]['id']],
                'drivers': [available_drivers[0]['id']],
                'soldiers': [s['id'] for s in available_soldiers[:7]],
                'mahlaka_id': 'pluga'
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
                # כוננות א' תמיד פלוגתית
                return {
                    'commanders': [available_commanders[0]['id']],
                    'drivers': [available_drivers[0]['id']],
                    'soldiers': [s['id'] for s in available_soldiers[:7]],
                    'mahlaka_id': 'pluga'
                }

        # 🔧 המערכת תמיד מצליחה! משתמשים בכל מי שזמין בלי בדיקות מנוחה
        all_people = all_commanders + all_drivers + all_soldiers
        all_people.sort(key=lambda x: (
            0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
        ))

        final_commanders = [all_people.pop(0)['id']] if all_people else []
        final_drivers = [all_people.pop(0)['id']] if all_people else []
        final_soldiers = [all_people.pop(0)['id'] for _ in range(min(7, len(all_people)))]

        # כוננות א' תמיד פלוגתית
        return {
            'commanders': final_commanders,
            'drivers': final_drivers,
            'soldiers': final_soldiers,
            'mahlaka_id': 'pluga'
        }

    def _try_build_standby_b_from_tasks(self, assign_data: Dict, all_commanders: List[Dict],
                                        all_soldiers: List[Dict], schedules: Dict) -> Dict:
        """ניסיון לבנות כוננות ב' מסיור שלישי + 3 שמירות

        לוקח:
        - מפקד מהסיור השלישי שהסתיים (לא 2 הראשונים!)
        - 3 שומרים מ-3 השמירות האחרונות

        Returns:
            Dict עם commanders, soldiers או None אם לא הצליח
        """
        # מצא סיורים ושמירות שהסתיימו
        all_people = all_commanders + all_soldiers
        finished_patrols = self.get_recently_finished_tasks_by_type(
            all_people, schedules, assign_data['day'], assign_data['start_hour'], ['סיור']
        )
        finished_guards = self.get_recently_finished_tasks_by_type(
            all_people, schedules, assign_data['day'], assign_data['start_hour'], ['שמירה']
        )

        # צריך לפחות 3 סיורים (לקחת את השלישי) ו-3 שמירות
        if len(finished_patrols) < 3 or len(finished_guards) < 3:
            return None

        # קח את הסיור השלישי (לא 2 הראשונים!)
        patrol_3 = finished_patrols[2]

        # מצא מפקד מהסיור השלישי
        commander_from_patrol = None
        for participant in patrol_3['participants']:
            if participant['role'] in ['מכ', 'ממ', 'סמל']:
                commander_from_patrol = participant
                break

        if not commander_from_patrol:
            return None

        # קח 3 שומרים מ-3 השמירות הראשונות
        guards_from_shifts = []
        for guard_shift in finished_guards[:3]:
            # קח שומר אחד מכל שמירה
            for participant in guard_shift['participants']:
                if participant['role'] not in ['מכ', 'ממ', 'סמל']:  # לא מפקד
                    guards_from_shifts.append(participant)
                    break  # רק אחד מכל שמירה

        if len(guards_from_shifts) < 3:
            return None

        # בדוק שהמפקד והשומרים זמינים לכוננות (לא משובצים)
        if not self.can_assign_at(schedules.get(commander_from_patrol['id'], []), assign_data['day'],
                                 assign_data['start_hour'], assign_data['length_in_hours'], 0):
            return None

        final_soldiers = []
        for guard in guards_from_shifts[:3]:
            if self.can_assign_at(schedules.get(guard['id'], []), assign_data['day'],
                                assign_data['start_hour'], assign_data['length_in_hours'], 0):
                final_soldiers.append(guard['id'])

        # בדוק שיש לפחות 3 שומרים זמינים
        if len(final_soldiers) < 3:
            return None

        return {
            'commanders': [commander_from_patrol['id']],
            'soldiers': final_soldiers[:3]
        }

    def assign_standby_b(self, assign_data: Dict, all_commanders: List[Dict],
                        all_soldiers: List[Dict], schedules: Dict) -> Dict:
        """שיבוץ כוננות ב - לוקח מפקד מסיור 3 + 3 שומרים אם האופציה מופעלת"""

        # קח את הערך מהתבנית, ואם לא קיים שם - קח מההגדרה הכללית
        reuse_from_template = assign_data.get('reuse_soldiers_for_standby', self.reuse_soldiers_for_standby)

        if reuse_from_template:
            # נסה לבנות כוננות מסיור שלישי + 3 שמירות
            result = self._try_build_standby_b_from_tasks(
                assign_data, all_commanders, all_soldiers, schedules
            )
            if result:
                # כוננות ב' תמיד פלוגתית (לוקחת אנשים ממחלקות שונות)
                result['mahlaka_id'] = 'pluga'
                return result
            # אם לא הצלחנו לבנות - לא משלימים! החזר ריק
            return {'commanders': [], 'soldiers': [], 'mahlaka_id': 'pluga'}

        # שיבוץ רגיל - לא מסומן reuse
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
            # מיון לפי שעות מנוחה - מי שנח יותר קודם
            available_commanders.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
            available_soldiers.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )

            # כוננות ב' תמיד פלוגתית
            return {
                'commanders': [available_commanders[0]['id']],
                'soldiers': [s['id'] for s in available_soldiers[:3]],
                'mahlaka_id': 'pluga'
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
                # כוננות ב' תמיד פלוגתית
                return {
                    'commanders': [available_commanders[0]['id']],
                    'soldiers': [s['id'] for s in available_soldiers[:3]],
                    'mahlaka_id': 'pluga'
                }

        # 🔧 המערכת תמיד מצליחה! משתמשים בכל מי שזמין בלי בדיקות מנוחה
        all_people = all_commanders + all_soldiers
        all_people.sort(key=lambda x: (
            0 if x['role'] == 'מכ' else 1 if x['role'] == 'סמל' else 2
        ))

        final_commanders = [all_people.pop(0)['id']] if all_people else []
        final_soldiers = [all_people.pop(0)['id'] for _ in range(min(3, len(all_people)))]

        # כוננות ב' תמיד פלוגתית
        return {
            'commanders': final_commanders,
            'soldiers': final_soldiers,
            'mahlaka_id': 'pluga'
        }

    def assign_operations(self, assign_data: Dict, all_people: List[Dict],
                         schedules: Dict) -> Dict:
        """שיבוץ חמל - דורש הסמכה, עם מקסימום שעות מנוחה"""
        # קבל את שם ההסמכה הנדרשת מהתבנית (או ברירת מחדל 'חמל')
        required_cert = assign_data.get('requires_certification', 'חמל')

        # חשוב: רק חיילים רגילים (לא מפקדים) יכולים לשמש בחמ"ל
        certified = [
            p for p in all_people
            if p.get('role') not in ['ממ', 'מכ', 'סמל', 'מפ'] and
               required_cert in p.get('certifications', []) and
               self.can_assign_at(schedules.get(p['id'], []), assign_data['day'],
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
            selected_person = certified[0]
            return {
                'soldiers': [selected_person['id']],
                'mahlaka_id': selected_person.get('mahlaka_id')
            }

        if self.emergency_mode:
            reduced_rest = self.min_rest_hours // 2
            # גם במצב חירום - רק חיילים רגילים (לא מפקדים) בחמ"ל
            certified = [
                p for p in all_people
                if p.get('role') not in ['ממ', 'מכ', 'סמל', 'מפ'] and
                   required_cert in p.get('certifications', []) and
                   self.can_assign_at(schedules.get(p['id'], []), assign_data['day'],
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
                selected_person = certified[0]
                return {
                    'soldiers': [selected_person['id']],
                    'mahlaka_id': selected_person.get('mahlaka_id')
                }

        # 🔧 המערכת תמיד מצליחה! אם אין מוסמך חמל - ניקח מי שזמין
        # אבל עדיין צריך לבדוק שהוא לא משובץ באותו זמן!
        available_people = [
            p for p in all_people
            if self.can_assign_at(schedules.get(p['id'], []), assign_data['day'],
                                 assign_data['start_hour'], assign_data['length_in_hours'],
                                 0)  # אפס מנוחה - רק בדיקת חפיפה
        ]

        if available_people:
            # עדיפות: מי שנח הכי הרבה
            available_people.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
            selected_person = available_people[0]
            return {
                'soldiers': [selected_person['id']],
                'mahlaka_id': selected_person.get('mahlaka_id')
            }

        return {'soldiers': [], 'mahlaka_id': None}

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
            selected_soldiers = available[:num_needed]
            # בדוק אם כולם מאותה מחלקה - אם לא, זה פלוגתי (צהוב)
            mahlaka_ids = set(s.get('mahlaka_id') for s in selected_soldiers)
            mahlaka_id = mahlaka_ids.pop() if len(mahlaka_ids) == 1 else 'pluga'
            return {
                'soldiers': [s['id'] for s in selected_soldiers],
                'mahlaka_id': mahlaka_id
            }

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
                selected_soldiers = available[:num_needed]
                # בדוק אם כולם מאותה מחלקה - אם לא, זה פלוגתי (צהוב)
                mahlaka_ids = set(s.get('mahlaka_id') for s in selected_soldiers)
                mahlaka_id = mahlaka_ids.pop() if len(mahlaka_ids) == 1 else 'pluga'
                return {
                    'soldiers': [s['id'] for s in selected_soldiers],
                    'mahlaka_id': mahlaka_id
                }

        # 🔧 המערכת תמיד מצליחה! אם אין מספיק - נשתמש במי שזמין
        # אבל עדיין צריך לבדוק שהוא לא משובץ באותו זמן!
        available_people = [
            s for s in all_soldiers
            if self.can_assign_at(schedules.get(s['id'], []), assign_data['day'],
                                 assign_data['start_hour'], assign_data['length_in_hours'],
                                 0)  # אפס מנוחה - רק בדיקת חפיפה
        ]

        if available_people:
            # עדיפות: מי שנח הכי הרבה
            available_people.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
            num_to_assign = min(num_needed, len(available_people))
            # אזהרה רק אם חסרים יותר מ-30% מהחיילים הנדרשים (או לפחות 2 חיילים)
            shortage = num_needed - num_to_assign
            if shortage >= 2 or (shortage > 0 and shortage / num_needed > 0.3):
                self.warnings.append(f"⚠️ {assign_data['name']}: שובצו רק {num_to_assign} מתוך {num_needed} חיילים")
            selected_soldiers = available_people[:num_to_assign]
            # בדוק אם כולם מאותה מחלקה - אם לא, זה פלוגתי (צהוב)
            mahlaka_ids = set(s.get('mahlaka_id') for s in selected_soldiers)
            mahlaka_id = mahlaka_ids.pop() if len(mahlaka_ids) == 1 else 'pluga'
            return {
                'soldiers': [s['id'] for s in selected_soldiers],
                'mahlaka_id': mahlaka_id
            }

        # ממש אין אף אחד - נחזיר ריק (אבל לא Exception!)
        return {'soldiers': [], 'mahlaka_id': 'pluga'}
    
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
            selected_soldier = available[0]
            return {
                'soldiers': [selected_soldier['id']],
                'mahlaka_id': selected_soldier.get('mahlaka_id')
            }

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

        # 🔧 המערכת תמיד מצליחה! ניקח מי שזמין
        # אבל עדיין צריך לבדוק שהוא לא משובץ באותו זמן!
        available_people = [
            p for p in all_people
            if self.can_assign_at(schedules.get(p['id'], []), assign_data['day'],
                                 assign_data['start_hour'], assign_data['length_in_hours'],
                                 0)  # אפס מנוחה - רק בדיקת חפיפה
        ]

        if available_people:
            # עדיפות: מי שנח הכי הרבה
            available_people.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
            return {'soldiers': [available_people[0]['id']]}

        return {'soldiers': []}
    
    def assign_shalaz(self, assign_data: Dict, all_soldiers: List[Dict], 
                     schedules: Dict) -> Dict:
        """של״ז - 24 שעות"""
        return self.assign_guard(assign_data, all_soldiers, schedules)
    
    def assign_duty_officer(self, assign_data: Dict, all_commanders: List[Dict],
                           schedules: Dict) -> Dict:
        """קצין תורן - מפקד בכיר (רק מכ או ממ), עם מקסימום שעות מנוחה"""
        # סינון: רק מכ או ממ (לא סמל!)
        senior = [
            c for c in all_commanders
            if c['role'] in ['ממ', 'מכ'] and
               self.can_assign_at(schedules.get(c['id'], []), assign_data['day'],
                                  assign_data['start_hour'], assign_data['length_in_hours'],
                                  self.min_rest_hours)
        ]

        if senior:
            # מיון: עדיפות למכים, אחר כך לפי מנוחה
            def priority_key(commander):
                # מכ מקבל בונוס גבוה
                role_priority = 10000 if commander['role'] == 'מכ' else 0
                rest_hours = self.calculate_rest_hours(
                    schedules.get(commander['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                )
                return role_priority + rest_hours

            senior.sort(key=priority_key, reverse=True)
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

        # 🔧 המערכת תמיד מצליחה! ניקח מפקד זמין
        # אבל עדיין צריך לבדוק שהוא לא משובץ באותו זמן!
        available_commanders = [
            c for c in all_commanders
            if self.can_assign_at(schedules.get(c['id'], []), assign_data['day'],
                                 assign_data['start_hour'], assign_data['length_in_hours'],
                                 0)  # אפס מנוחה - רק בדיקת חפיפה
        ]

        if available_commanders:
            # עדיפות: מי שנח הכי הרבה
            available_commanders.sort(
                key=lambda x: self.calculate_rest_hours(
                    schedules.get(x['id'], []),
                    assign_data['day'],
                    assign_data['start_hour']
                ),
                reverse=True
            )
            return {'commanders': [available_commanders[0]['id']]}

        return {'commanders': []}
