"""
Setup Script for Shavzak System
"""
import os
import sys

def check_python():
    """בדיקת גרסת Python"""
    print("🔍 בודק Python...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ נדרש!")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def install_requirements():
    """התקנת תלויות"""
    print("\n📦 מתקין תלויות...")
    result = os.system(f"{sys.executable} -m pip install -r requirements.txt")
    if result == 0:
        print("✅ תלויות הותקנו!")
        return True
    print("❌ שגיאה בהתקנה")
    return False

def init_database():
    """אתחול מסד נתונים"""
    print("\n💾 מאתחל מסד נתונים...")
    try:
        from models import init_db
        init_db()
        print("✅ מסד נתונים אותחל!")
        return True
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        return False

def main():
    print("=" * 70)
    print("🎖️  Shavzak System - Setup")
    print("=" * 70)
    
    if not check_python():
        sys.exit(1)
    
    if not install_requirements():
        sys.exit(1)
    
    if not init_database():
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✅ Setup הושלם!")
    print("=" * 70)
    print("\n📋 להפעלה:")
    print("   python api.py")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
