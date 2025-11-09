from typing import Dict, List
from person_schedule import PersonSchedule
from datetime import datetime

class DisplayUtils:
    """כלים להצגה יפה של לוחות זמנים"""
    
    @staticmethod
    def print_personal_schedule(person, schedule: PersonSchedule, days: int = 7):
        """מדפיס לוח זמנים אישי"""
        print(f"\n{'='*70}")
        print(f"📋 לוח זמנים אישי: {person.name} ({person.role})")
        print(f"{'='*70}\n")
        
        for day in range(days):
            day_assignments = schedule.get_assignments_by_day(day)
            if day_assignments:
                print(f"\n📅 יום {day + 1} - {schedule.get_total_hours(day)} שעות")
                print("─" * 50)
                
                for day_num, start, end, name, assign_type in day_assignments:
                    print(f"  ⏰ {start:02d}:00 - {end:02d}:00 | {name} ({assign_type.value})")
    
    @staticmethod
    def export_to_text(schedules: Dict, filename: str = "shavzak.txt"):
        """יצוא ללוח זמנים לקובץ טקסט"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("לוח שיבוץ פלוגתי\n")
            f.write(f"תאריך הפקה: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write("=" * 80 + "\n\n")
            
            for person, schedule in schedules.items():
                if schedule.get_total_hours() > 0:
                    f.write(f"\n{person.name} ({person.role})\n")
                    f.write("─" * 50 + "\n")
                    
                    for day_num, start, end, name, assign_type in schedule.assignments:
                        f.write(f"יום {day_num + 1} | {start:02d}:00-{end:02d}:00 | {name}\n")
                    
                    f.write(f"סה״כ: {schedule.get_total_hours()} שעות\n")
        
        print(f"✓ הקובץ נשמר ב: {filename}")
    
    @staticmethod
    def print_daily_summary(schedules: Dict, day: int):
        """סיכום יומי - מי עובד מה"""
        print(f"\n{'='*70}")
        print(f"📊 סיכום יום {day + 1}")
        print(f"{'='*70}\n")
        
        assignments_by_type = {}
        
        for person, schedule in schedules.items():
            for day_num, start, end, name, assign_type in schedule.get_assignments_by_day(day):
                type_name = assign_type.value
                if type_name not in assignments_by_type:
                    assignments_by_type[type_name] = []
                assignments_by_type[type_name].append({
                    'person': person.name,
                    'role': person.role,
                    'time': f"{start:02d}:00-{end:02d}:00"
                })
        
        for assign_type, people in sorted(assignments_by_type.items()):
            print(f"\n📌 {assign_type}")
            print("─" * 50)
            for p in people:
                print(f"  {p['time']} | {p['person']} ({p['role']})")
    
    @staticmethod
    def print_statistics(schedules: Dict, days: int):
        """סטטיסטיקות כלליות"""
        print(f"\n{'='*70}")
        print(f"📊 סטטיסטיקות - {days} ימים")
        print(f"{'='*70}\n")
        
        total_hours = {}
        for person, schedule in schedules.items():
            hours = schedule.get_total_hours()
            if hours > 0:
                total_hours[person.name] = {
                    'hours': hours,
                    'role': person.role,
                    'avg_per_day': hours / days
                }
        
        print("🏆 עשירית הכי עסוקים:")
        print("─" * 50)
        sorted_workers = sorted(total_hours.items(), key=lambda x: x[1]['hours'], reverse=True)
        for i, (name, data) in enumerate(sorted_workers[:10], 1):
            print(f"{i:2}. {name:20} | {data['hours']:3} שעות | ממוצע {data['avg_per_day']:.1f} שעות/יום")
        
        print("\n💤 עשירית הכי פחות עסוקים:")
        print("─" * 50)
        for i, (name, data) in enumerate(sorted_workers[-10:], 1):
            print(f"{i:2}. {name:20} | {data['hours']:3} שעות | ממוצע {data['avg_per_day']:.1f} שעות/יום")
        
        avg_hours = sum(d['hours'] for d in total_hours.values()) / len(total_hours)
        print(f"\n📊 ממוצע שעות לחייל: {avg_hours:.1f} שעות")