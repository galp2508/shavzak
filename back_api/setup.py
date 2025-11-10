"""
Quick Setup Script for Shavzak System
הרצה: python setup.py
"""
import os
import sys

def print_header():
    print("=" * 70)
    print("🎖️  Shavzak System - Setup Script")
    print("=" * 70)
    print()

def check_python_version():
    """בדיקת גרסת Python"""
    print("🔍 בודק גרסת Python...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ נדרש!")
        print(f"   גרסה נוכחית: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} - טוב!")
    return True

def install_requirements():
    """התקנת תלויות"""
    print("\n📦 מתקין תלויות...")
    result = os.system(f"{sys.executable} -m pip install -r requirements.txt")
    if result == 0:
        print("✅ תלויות הותקנו בהצלחה!")
        return True
    else:
        print("❌ שגיאה בהתקנת תלויות")
        return False

def create_env_file():
    """יצירת קובץ .env"""
    print("\n🔧 יוצר קובץ .env...")
    
    if os.path.exists('.env'):
        print("⚠️  קובץ .env כבר קיים")
        response = input("   להחליף? (y/n): ")
        if response.lower() != 'y':
            print("   משאיר את הקובץ הקיים")
            return True
    
    try:
        with open('.env.example', 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ קובץ .env נוצר!")
        print("⚠️  זכור לשנות את SECRET_KEY לפני ייצור!")
        return True
    except Exception as e:
        print(f"❌ שגיאה ביצירת .env: {e}")
        return False

def initialize_database():
    """אתחול מסד נתונים"""
    print("\n💾 מאתחל מסד נתונים...")
    
    try:
        from models import init_db
        init_db()
        print("✅ מסד נתונים אותחל בהצלחה!")
        return True
    except Exception as e:
        print(f"❌ שגיאה באתחול DB: {e}")
        return False

def print_next_steps():
    """הדרכה לשלבים הבאים"""
    print("\n" + "=" * 70)
    print("🎉 Setup הושלם בהצלחה!")
    print("=" * 70)
    print("\n📋 שלבים הבאים:\n")
    print("1. הפעל את השרת:")
    print("   python api.py")
    print("\n2. פתח דפדפן/Postman והירשם:")
    print("   POST http://localhost:5000/api/register")
    print("   Body: {")
    print('     "username": "commander1",')
    print('     "password": "yourPassword",')
    print('     "full_name": "Your Name"')
    print("   }")
    print("\n3. קרא את התיעוד המלא:")
    print("   API_DOCUMENTATION.md")
    print("\n4. צור פלוגה, מחלקות וחיילים")
    print("\n" + "=" * 70)
    print("בהצלחה! 🚀")
    print("=" * 70)

def main():
    print_header()
    
    # בדיקות
    if not check_python_version():
        sys.exit(1)
    
    # התקנה
    if not install_requirements():
        print("\n⚠️  המשך בכל זאת? (y/n): ", end="")
        if input().lower() != 'y':
            sys.exit(1)
    
    # קונפיגורציה
    if not create_env_file():
        print("\n⚠️  המשך בכל זאת? (y/n): ", end="")
        if input().lower() != 'y':
            sys.exit(1)
    
    # DB
    if not initialize_database():
        print("\n⚠️  המשך בכל זאת? (y/n): ", end="")
        if input().lower() != 'y':
            sys.exit(1)
    
    # סיום
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup בוטל על ידי המשתמש")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ שגיאה לא צפויה: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
