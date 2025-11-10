"""
Example Usage - Shavzak API
דוגמה מלאה לשימוש במערכת
"""
import requests
import json
from datetime import datetime, timedelta

BASE = "http://localhost:5000/api"

class ShavzakClient:
    def __init__(self):
        self.token = None
        self.pluga_id = None
    
    def print_response(self, response, title=""):
        """הדפסה יפה"""
        print(f"\n{'='*70}")
        print(f"📋 {title}")
        print(f"{'='*70}")
        print(f"Status: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print(response.text)
        print(f"{'='*70}\n")
    
    def register(self, username, password, full_name):
        """רישום"""
        response = requests.post(f"{BASE}/register", json={
            "username": username,
            "password": password,
            "full_name": full_name
        })
        self.print_response(response, "Register")
        
        if response.status_code == 201:
            self.token = response.json()['token']
            print("✅ נרשמת בהצלחה!")
        
        return response
    
    def login(self, username, password):
        """התחברות"""
        response = requests.post(f"{BASE}/login", json={
            "username": username,
            "password": password
        })
        self.print_response(response, "Login")
        
        if response.status_code == 200:
            self.token = response.json()['token']
            self.pluga_id = response.json()['user'].get('pluga_id')
            print("✅ התחברת בהצלחה!")
        
        return response
    
    def headers(self):
        """Headers עם token"""
        if not self.token:
            raise Exception("אין token - עשה login קודם")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def create_pluga(self, name, gdud="", color="#FFFFFF"):
        """יצירת פלוגה"""
        response = requests.post(f"{BASE}/plugot", 
            json={"name": name, "gdud": gdud, "color": color},
            headers=self.headers()
        )
        self.print_response(response, "Create Pluga")
        
        if response.status_code == 201:
            self.pluga_id = response.json()['pluga']['id']
            print(f"✅ פלוגה נוצרה! ID: {self.pluga_id}")
        
        return response
    
    def create_mahlaka(self, number, color="#FFFFFF"):
        """יצירת מחלקה"""
        response = requests.post(f"{BASE}/mahalkot",
            json={"number": number, "color": color, "pluga_id": self.pluga_id},
            headers=self.headers()
        )
        self.print_response(response, f"Create Mahlaka {number}")
        return response
    
    def create_soldier(self, name, role, mahlaka_id, kita=None, **kwargs):
        """יצירת חייל"""
        response = requests.post(f"{BASE}/soldiers",
            json={"name": name, "role": role, "mahlaka_id": mahlaka_id, 
                  "kita": kita, **kwargs},
            headers=self.headers()
        )
        self.print_response(response, f"Create Soldier: {name}")
        return response
    
    def create_template(self, name, assignment_type, length_in_hours, 
                       times_per_day, **kwargs):
        """יצירת תבנית"""
        response = requests.post(
            f"{BASE}/plugot/{self.pluga_id}/assignment-templates",
            json={"name": name, "assignment_type": assignment_type,
                  "length_in_hours": length_in_hours, "times_per_day": times_per_day,
                  **kwargs},
            headers=self.headers()
        )
        self.print_response(response, f"Create Template: {name}")
        return response
    
    def create_shavzak(self, name, start_date, days_count):
        """יצירת שיבוץ"""
        response = requests.post(f"{BASE}/shavzakim",
            json={"name": name, "start_date": start_date, 
                  "days_count": days_count, "pluga_id": self.pluga_id},
            headers=self.headers()
        )
        self.print_response(response, f"Create Shavzak: {name}")
        return response
    
    def generate_shavzak(self, shavzak_id):
        """הרצת אלגוריתם"""
        response = requests.post(f"{BASE}/shavzakim/{shavzak_id}/generate",
            headers=self.headers()
        )
        self.print_response(response, "Generate Shavzak")
        return response
    
    def get_shavzak(self, shavzak_id):
        """קבלת שיבוץ"""
        response = requests.get(f"{BASE}/shavzakim/{shavzak_id}",
            headers=self.headers()
        )
        self.print_response(response, "Get Shavzak")
        return response


def full_demo():
    """דוגמה מלאה"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║       🎖️  Shavzak System - Full Demo                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    client = ShavzakClient()
    
    # 1. רישום
    print("\n📝 שלב 1: רישום מ\"פ")
    client.register("commander1", "pass123", "משה כהן")
    
    # 2. יצירת פלוגה
    print("\n🏢 שלב 2: יצירת פלוגה")
    client.create_pluga("פלוגה ב", "גדוד פנתר", "#BF092F")
    
    # 3. יצירת מחלקות
    print("\n📦 שלב 3: יצירת 4 מחלקות")
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    mahlaka_ids = []
    
    for i, color in enumerate(colors, 1):
        response = client.create_mahlaka(i, color)
        if response.status_code == 201:
            mahlaka_ids.append(response.json()['mahlaka']['id'])
    
    # 4. הוספת חיילים
    print("\n👥 שלב 4: הוספת חיילים")
    
    soldiers = [
        # מחלקה 1
        {"name": "משה לוי", "role": "ממ", "mahlaka_id": mahlaka_ids[0]},
        {"name": "יוסי כהן", "role": "מכ", "mahlaka_id": mahlaka_ids[0], "kita": "א"},
        {"name": "דוד אברהם", "role": "לוחם", "mahlaka_id": mahlaka_ids[0], "kita": "א"},
        {"name": "אבי ישראל", "role": "לוחם", "mahlaka_id": mahlaka_ids[0], "kita": "א"},
        {"name": "שלום יצחק", "role": "נהג", "mahlaka_id": mahlaka_ids[0], "kita": "א",
         "certifications": ["נהג"]},
        
        # מחלקה 2
        {"name": "רון שמש", "role": "ממ", "mahlaka_id": mahlaka_ids[1]},
        {"name": "עומר זהבי", "role": "מכ", "mahlaka_id": mahlaka_ids[1], "kita": "ב"},
        {"name": "תום סער", "role": "לוחם", "mahlaka_id": mahlaka_ids[1], "kita": "ב"},
        {"name": "גל מור", "role": "לוחם", "mahlaka_id": mahlaka_ids[1], "kita": "ב"},
        {"name": "נועם ברק", "role": "נהג", "mahlaka_id": mahlaka_ids[1], "kita": "ב",
         "certifications": ["נהג"]},
        
        # מחלקה 3
        {"name": "אלי כהן", "role": "סמל", "mahlaka_id": mahlaka_ids[2]},
        {"name": "דני לב", "role": "לוחם", "mahlaka_id": mahlaka_ids[2], "kita": "ג"},
        {"name": "יובל ארז", "role": "לוחם", "mahlaka_id": mahlaka_ids[2], "kita": "ג"},
        {"name": "אור גולן", "role": "נהג", "mahlaka_id": mahlaka_ids[2], "kita": "ג",
         "certifications": ["נהג", "חמל"]},
        
        # מחלקה 4
        {"name": "איתי בן", "role": "סמל", "mahlaka_id": mahlaka_ids[3]},
        {"name": "רועי דור", "role": "לוחם", "mahlaka_id": mahlaka_ids[3], "kita": "ד"},
        {"name": "עידו נוי", "role": "לוחם", "mahlaka_id": mahlaka_ids[3], "kita": "ד"},
        {"name": "גיא פז", "role": "נהג", "mahlaka_id": mahlaka_ids[3], "kita": "ד",
         "certifications": ["נהג"]},
    ]
    
    for soldier in soldiers:
        client.create_soldier(**soldier)
    
    # 5. יצירת תבניות
    print("\n📋 שלב 5: יצירת תבניות משימות")
    
    templates = [
        {
            "name": "סיור",
            "assignment_type": "סיור",
            "length_in_hours": 8,
            "times_per_day": 3,
            "commanders_needed": 1,
            "drivers_needed": 1,
            "soldiers_needed": 2,
            "same_mahlaka_required": True
        },
        {
            "name": "שמירה",
            "assignment_type": "שמירה",
            "length_in_hours": 4,
            "times_per_day": 6,
            "commanders_needed": 0,
            "drivers_needed": 0,
            "soldiers_needed": 1
        },
        {
            "name": "כוננות א",
            "assignment_type": "כוננות א",
            "length_in_hours": 8,
            "times_per_day": 3,
            "commanders_needed": 1,
            "drivers_needed": 1,
            "soldiers_needed": 7
        }
    ]
    
    for template in templates:
        client.create_template(**template)
    
    # 6. יצירת שיבוץ
    print("\n📅 שלב 6: יצירת שיבוץ")
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    response = client.create_shavzak("שיבוץ שבוע 46", start_date, 7)
    
    if response.status_code == 201:
        shavzak_id = response.json()['shavzak']['id']
        
        # 7. הרצת אלגוריתם
        print("\n🤖 שלב 7: הרצת אלגוריתם השיבוץ")
        client.generate_shavzak(shavzak_id)
        
        # 8. צפייה בתוצאות
        print("\n📊 שלב 8: צפייה בשיבוץ")
        client.get_shavzak(shavzak_id)
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    ✅ Demo Completed!                        ║
║                                                              ║
║  כעת יש לך מערכת מלאה עם:                                  ║
║  • פלוגה אחת                                                ║
║  • 4 מחלקות                                                 ║
║  • 18 חיילים                                                ║
║  • 3 תבניות משימות                                          ║
║  • שיבוץ מלא ל-7 ימים                                       ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    try:
        # בדיקת חיבור
        try:
            response = requests.get(f"{BASE}/health", timeout=2)
            if response.status_code != 200:
                print("❌ השרת לא עונה")
                exit(1)
        except:
            print("❌ לא ניתן להתחבר לשרת!")
            print("   הרץ: python api.py")
            exit(1)
        
        # הרצת Demo
        full_demo()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo בוטל")
    except Exception as e:
        print(f"\n\n❌ שגיאה: {e}")
