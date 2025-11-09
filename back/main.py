import pluga
from shavzak_manager import shavzak_manager
from datetime import datetime
import ctypes

LF_FACESIZE = 32
STD_OUTPUT_HANDLE = -11

class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

class CONSOLE_FONT_INFOEX(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong),
                ("nFont", ctypes.c_ulong),
                ("dwFontSize", COORD),
                ("FontFamily", ctypes.c_uint),
                ("FontWeight", ctypes.c_uint),
                ("FaceName", ctypes.c_wchar * LF_FACESIZE)]

def set_console_font(font_name: str = "Consolas", font_size: int = 16):
    font = CONSOLE_FONT_INFOEX()
    font.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX)
    font.nFont = 12
    font.dwFontSize.X = 11
    font.dwFontSize.Y = 18
    font.FontFamily = 54
    font.FontWeight = 400
    font.FaceName = "Lucida Console"

    handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    ctypes.windll.kernel32.SetCurrentConsoleFontEx(
            handle, ctypes.c_long(False), ctypes.pointer(font))

def main():
    set_console_font()
    print("🎖️  מערכת שיבוץ מתקדמת - IDF Assignment System")
    print("=" * 70)
    
    print("\n📋 שלב 1: יצירת הפלוגה")
    my_pluga = pluga.pluga(name="פלוגה ב", gdud="פנתר", 
                           color="#BF092F", number_of_mahalkha=4)
    
    print("\n📋 שלב 2: יצירת מנהל השיבוץ")
    days_to_plan = int(input("כמה ימים קדימה לתכנן? (ברירת מחדל: 7): ") or "7")
    manager = shavzak_manager(pluga_instance=my_pluga, days_ahead=days_to_plan)
    
    print("\n📋 שלב 3: הגדרת סוגי משימות")
    use_defaults = input("להשתמש במשימות ברירת מחדל? (y/n): ").lower()
    
    if use_defaults == 'y':
        manager.setup_default_assignments()
    else:
        print("הוספת משימות ידנית - בפיתוח...")
    
    print("\n📋 שלב 4: יצירת משבצות זמן ובדיקת כוח אדם")
    manager.create_time_slots()
    
    try:
        manager.validate_manpower_requirements()
    except Exception as e:
        print(f"\n❌ {e}")
        return
    
    print("\n📋 שלב 5: ביצוע שיבוץ חכם")
    start_date_str = input("תאריך התחלה (DD.MM.YYYY, או Enter להיום): ").strip()
    
    if start_date_str:
        from gdatetime import str_to_gdate
        start_date = str_to_gdate(start_date_str)
    else:
        start_date = datetime.now()
    
    try:
        schedules = manager.assign_soldiers_smart(start_date=start_date)
        
        print("\n📋 שלב 6: הצגת תוצאות")
        print("\nאפשרויות הצגה:")
        print("1. לוח זמנים מלא (כל הימים)")
        print("2. לוח זמנים ליום ספציפי")
        print("3. יצוא לקובץ")
        
        choice = input("\nבחר אפשרות (1-3): ").strip()
        
        if choice == '1':
            manager.display_company_schedule()
        elif choice == '2':
            day = int(input(f"איזה יום? (1-{days_to_plan}): ")) - 1
            manager.display_company_schedule(day=day)
        elif choice == '3':
            from display_utils import DisplayUtils
            DisplayUtils.export_to_text(schedules, "shavzak_output.txt")
        
        print("\n✅ שיבוץ הושלם בהצלחה!")
        
    except Exception as e:
        print(f"\n❌ שגיאה בשיבוץ: {e}")
        print("\nטיפים:")
        print("- הוסף עוד חיילים זמינים")
        print("- הקטן את מספר הימים")
        print("- בדוק שב\"נים")

if __name__ == "__main__":
    main()