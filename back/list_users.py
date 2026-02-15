"""
סקריפט לצפייה במשתמשים ואיפוס סיסמאות
שימוש:
  python back/list_users.py                    # הצגת כל המשתמשים
  python back/list_users.py reset <username> <new_password>  # איפוס סיסמה
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User
from config import Config

DB_PATH = os.path.join(os.path.dirname(__file__), Config.DATABASE_PATH)
engine = create_engine(f'sqlite:///{DB_PATH}')
Session = sessionmaker(bind=engine)
session = Session()


def list_users():
    """הצגת כל המשתמשים"""
    users = session.query(User).all()
    if not users:
        print("אין משתמשים במערכת")
        return

    print(f"\n{'='*70}")
    print(f"{'ID':>4} | {'שם משתמש':<20} | {'שם מלא':<20} | {'תפקיד':<6} | {'כניסה אחרונה':<20}")
    print(f"{'='*70}")
    for u in users:
        last_login = u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else 'אף פעם'
        print(f"{u.id:>4} | {u.username:<20} | {u.full_name:<20} | {u.role:<6} | {last_login:<20}")
    print(f"{'='*70}")
    print(f"סה\"כ: {len(users)} משתמשים\n")
    print("הערה: הסיסמאות מוצפנות ב-bcrypt ולא ניתנות לשחזור.")
    print("לאיפוס סיסמה: python back/list_users.py reset <username> <new_password>")


def reset_password(username, new_password):
    """איפוס סיסמה למשתמש"""
    user = session.query(User).filter_by(username=username).first()
    if not user:
        print(f"❌ משתמש '{username}' לא נמצא")
        return

    user.set_password(new_password)
    session.commit()
    print(f"✅ סיסמה של '{username}' ({user.full_name}) אופסה בהצלחה")


if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == 'reset':
        reset_password(sys.argv[2], sys.argv[3])
    else:
        list_users()

session.close()
