"""
Example Usage Script - Shavzak API
דוגמת שימוש מלאה במערכת
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api"

class ShavzakClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.pluga_id = None
    
    def print_response(self, response, title="Response"):
        """הדפסה יפה של תגובת API"""
        print(f"\n{'='*70}")
        print(f"📋 {title}")
        print(f"{'='*70}")
        print(f"Status: {response.status_code}")
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(response.text)
        print(f"{'='*70}\n")
    
    def register(self, username, password, full_name):
        """רישום משתמש"""
        url = f"{self.base_url}/register"
        data = {
            "username": username,
            "password": password,
            "full_name": full_name
        }
        response = requests.post(url, json=data)
        self.print_response(response, "Register")
        
        if response.status_code == 201:
            result = response.json()
            self.token = result['token']
            self.user = result['user']
            print("✅ נרשמת בהצלחה!")
        
        return response
    
    def login(self, username, password):
        """התחברות"""
        url = f"{self.base_url}/login"
        data = {
            "username": username,
            "password": password
        }
        response = requests.post(url, json=data)
        self.print_response(response, "Login")
        
        if response.status_code == 200:
            result = response.json()
            self.token = result['token']
            self.user = result['user']
            self.pluga_id = result['user'].get('pluga_id')
            print("✅ התחברת בהצלחה!")
        
        return response
    
    def get_headers(self):
        """קבלת headers עם token"""
        if not self.token:
            raise Exception("אין token - עשה login קודם")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def create_pluga(self, name, gdud="", color="#FFFFFF"):
        """יצירת פלוגה"""
        url = f"{self.base_url}/plugot"
        data = {
            "name": name,
            "gdud": gdud,
            "color": color
        }
        response = requests.post(url, json=data, headers=self.get_headers())
        self.print_response(response, "Create Pluga")
        
        if response.status_code == 201:
            result = response.json()
            self.pluga_id = result['pluga']['id']
            print(f"✅ פלוגה נוצרה! ID: {self.pluga_id}")
        
        return response
    
    def create_mahlaka(self, number, color="#FFFFFF"):
        """יצירת מחלקה"""
        url = f"{self.base_url}/mahalkot"
        data = {
            "number": number,
            "color": color,
            "pluga_id": self.pluga_id
        }
        response = requests.post(url, json=data, headers=self.get_headers())
        self.print_response(response, f"Create Mahlaka {number}")
        return response
    
    def create_soldier(self, name, role, mahlaka_id, kita=None, **kwargs):
        """יצירת חייל"""
        url = f"{self.base_url}/soldiers"
        data = {
            "name": name,
            "role": role,
            "mahlaka_id": mahlaka_id,
            "kita": kita,
            **kwargs
        }
        response = requests.post(url, json=data, headers=self.get_headers())
        self.print_response(response, f"Create Soldier: {name}")
        return response
    
    def create_assignment_template(self, name, assignment_type, length_in_hours, 
                                    times_per_day, **kwargs):
        """יצירת תבנית משימה"""
        url = f"{self.base_url}/plugot/{self.pluga_id}/assignment-templates"
        data = {
            "name": name,
            "assignment_type": assignment_type,
            "length_in_hours": length_in_hours,
            "times_per_day": times_per_day,
            **kwargs
        }
        response = requests.post(url, json=data, headers=self.get_headers())
        self.print_response(response, f"Create Template: {name}")
        return response
    
    def create_shavzak(self, name, start_date, days_count, **kwargs):
        """יצירת שיבוץ"""
        url = f"{self.base_url}/shavzakim"
        data = {
            "name": name,
            "start_date": start_date,
            "days_count": days_count,
            "pluga_id": self.pluga_id,
            **kwargs
        }
        response = requests.post(url, json=data, headers=self.get_headers())
        self.print_response(response, f"Create Shavzak: {name}")
        return response
    
    def get_stats(self):
        """סטטיסטיקות"""
        url = f"{self.base_url}/stats"
        response = requests.get(url, headers=self.get_headers())
        self.print_response(response, "Statistics")
        return response
    
    def list_mahalkot(self):
        """רשימת מחלקות"""
        url = f"{self.base_url}/plugot/{self.pluga_id}/mahalkot"
        response = requests.get(url, headers=self.get_headers())
        self.print_response(response, "List Mahalkot")
        return response


def full_demo():
    """דוגמה מלאה לשימוש במערכת"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║       🎖️  Shavzak System - Full Demo Script                 ║
    ║              הדגמה מלאה של המערכת                           ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    client = ShavzakClient()
    
    # שלב 1: רישום
    print("\n📝 שלב 1: רישום מ\"פ")
    client.register("commander1", "pass123", "משה כהן")
    
    # שלב 2: יצירת פלוגה
    print("\n🏢 שלב 2: יצירת פלוגה")
    client.create_pluga("פלוגה ב", "גדוד פנתר", "#BF092F")
    
    # שלב 3: יצירת מחלקות
    print("\n📦 שלב 3: יצירת 4 מחלקות")
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    mahlaka_ids = []
    
    for i, color in enumerate(colors, 1):
        response = client.create_mahlaka(i, color)
        if response.status_code == 201:
            mahlaka_id = response.json()['mahlaka']['id']
            mahlaka_ids.append(mahlaka_id)
    
    # שלב 4: הוספת חיילים
    print("\n👥 שלב 4: הוספת חיילים")
    
    soldiers_data = [
        # מחלקה 1
        {"name": "משה לוי", "role": "ממ", "mahlaka_id": mahlaka_ids[0], "kita": None},
        {"name": "יוסי כהן", "role": "מכ", "mahlaka_id": mahlaka_ids[0], "kita": "א"},
        {"name": "דוד אברהם", "role": "לוחם", "mahlaka_id": mahlaka_ids[0], "kita": "א"},
        {"name": "אבי ישראל", "role": "לוחם", "mahlaka_id": mahlaka_ids[0], "kita": "א"},
        {"name": "שלום יצחק", "role": "נהג", "mahlaka_id": mahlaka_ids[0], "kita": "א"},
        
        # מחלקה 2
        {"name": "רון שמש", "role": "ממ", "mahlaka_id": mahlaka_ids[1], "kita": None},
        {"name": "עומר זהבי", "role": "מכ", "mahlaka_id": mahlaka_ids[1], "kita": "ב"},
        {"name": "תום סער", "role": "לוחם", "mahlaka_id": mahlaka_ids[1], "kita": "ב"},
        {"name": "גל מור", "role": "לוחם", "mahlaka_id": mahlaka_ids[1], "kita": "ב"},
        {"name": "נועם ברק", "role": "נהג", "mahlaka_id": mahlaka_ids[1], "kita": "ב"},
    ]
    
    for soldier_data in soldiers_data:
        client.create_soldier(**soldier_data)
    
    # שלב 5: יצירת תבניות משימות
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
            "soldiers_needed": 1,
            "same_mahlaka_required": False
        },
        {
            "name": "כוננות א",
            "assignment_type": "כוננות א",
            "length_in_hours": 8,
            "times_per_day": 3,
            "commanders_needed": 1,
            "drivers_needed": 1,
            "soldiers_needed": 7,
            "same_mahlaka_required": False
        }
    ]
    
    for template in templates:
        client.create_assignment_template(**template)
    
    # שלב 6: יצירת שיבוץ
    print("\n📅 שלב 6: יצירת שיבוץ")
    
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    client.create_shavzak("שיבוץ שבוע 46", start_date, 7)
    
    # שלב 7: סטטיסטיקות
    print("\n📊 שלב 7: סטטיסטיקות")
    client.get_stats()
    
    # שלב 8: רשימת מחלקות
    print("\n📦 שלב 8: רשימת מחלקות")
    client.list_mahalkot()
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    ✅ Demo Completed!                        ║
    ║                   הדוגמה הושלמה בהצלחה!                    ║
    ║                                                              ║
    ║  כעת יש לך:                                                 ║
    ║  • משתמש מ"פ                                                ║
    ║  • פלוגה אחת                                                ║
    ║  • 4 מחלקות                                                 ║
    ║  • 10 חיילים                                                ║
    ║  • 3 תבניות משימות                                          ║
    ║  • שיבוץ אחד                                                ║
    ║                                                              ║
    ║  המשך לעבוד עם ה-API או התחבר מהאפליקציה!                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    try:
        # בדיקה שהשרת רץ
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code != 200:
                print("❌ השרת לא עונה כראוי")
                exit(1)
        except requests.exceptions.ConnectionError:
            print("❌ לא ניתן להתחבר לשרת!")
            print("   ודא שהשרת רץ: python api.py")
            exit(1)
        
        # הרצת Demo
        full_demo()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo בוטל על ידי המשתמש")
    except Exception as e:
        print(f"\n\n❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()
