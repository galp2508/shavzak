"""
Authentication & Authorization System
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from models import User

SECRET_KEY = "your-secret-key-change-in-production"  # יש לשנות בייצור!
ALGORITHM = "HS256"

def create_token(user):
    """יצירת JWT token"""
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'pluga_id': user.pluga_id,
        'mahlaka_id': user.mahlaka_id,
        'kita': user.kita,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token):
    """פענוח JWT token"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """דקורטור לבדיקת token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # "Bearer <token>"
            except IndexError:
                return jsonify({'error': 'פורמט token לא תקין'}), 401
        
        if not token:
            return jsonify({'error': 'חסר token'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Token לא תקף או פג תוקף'}), 401
        
        # הוספת המידע ל-kwargs
        kwargs['current_user'] = payload
        return f(*args, **kwargs)
    
    return decorated


def role_required(allowed_roles):
    """דקורטור לבדיקת הרשאות לפי תפקיד"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                return jsonify({'error': 'נדרש אימות'}), 401
            
            user_role = current_user.get('role')
            if user_role not in allowed_roles:
                return jsonify({'error': 'אין לך הרשאה לפעולה זו'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def can_edit_pluga(current_user, pluga_id):
    """בדיקה האם המשתמש יכול לערוך פלוגה"""
    if current_user['role'] == 'מפ' and current_user['pluga_id'] == pluga_id:
        return True
    return False


def can_view_pluga(current_user, pluga_id):
    """בדיקה האם המשתמש יכול לצפות בפלוגה"""
    # כולם יכולים לצפות בפלוגה שלהם
    if current_user['pluga_id'] == pluga_id:
        return True
    return False


def can_edit_mahlaka(current_user, mahlaka_id, session):
    """בדיקה האם המשתמש יכול לערוך מחלקה"""
    from models import Mahlaka
    
    # מ"פ יכול לערוך את כל המחלקות בפלוגה שלו
    if current_user['role'] == 'מפ':
        mahlaka = session.query(Mahlaka).filter_by(id=mahlaka_id).first()
        if mahlaka and mahlaka.pluga_id == current_user['pluga_id']:
            return True
    
    # מ"מ יכול לערוך את המחלקה שלו
    if current_user['role'] == 'ממ' and current_user['mahlaka_id'] == mahlaka_id:
        return True
    
    return False


def can_view_mahlaka(current_user, mahlaka_id, session):
    """בדיקה האם המשתמש יכול לצפות במחלקה"""
    from models import Mahlaka
    
    mahlaka = session.query(Mahlaka).filter_by(id=mahlaka_id).first()
    if not mahlaka:
        return False
    
    # כולם בפלוגה יכולים לצפות בכל המחלקות
    if mahlaka.pluga_id == current_user['pluga_id']:
        return True
    
    return False


def can_edit_soldier(current_user, soldier_id, session):
    """בדיקה האם המשתמש יכול לערוך חייל"""
    from models import Soldier
    
    soldier = session.query(Soldier).filter_by(id=soldier_id).first()
    if not soldier:
        return False
    
    # מ"פ יכול לערוך את כל החיילים בפלוגה
    if current_user['role'] == 'מפ':
        from models import Mahlaka
        mahlaka = session.query(Mahlaka).filter_by(id=soldier.mahlaka_id).first()
        if mahlaka and mahlaka.pluga_id == current_user['pluga_id']:
            return True
    
    # מ"מ יכול לערוך חיילים במחלקה שלו
    if current_user['role'] == 'ממ' and soldier.mahlaka_id == current_user['mahlaka_id']:
        return True
    
    # מ"כ יכול לערוך חיילים בכיתה שלו
    if current_user['role'] == 'מכ' and soldier.kita == current_user['kita'] and \
       soldier.mahlaka_id == current_user['mahlaka_id']:
        return True
    
    return False


def can_edit_kita(current_user, kita_name, mahlaka_id):
    """בדיקה האם המשתמש יכול לערוך כיתה"""
    # מ"פ יכול לערוך הכל
    if current_user['role'] == 'מפ':
        return True
    
    # מ"מ יכול לערוך כיתות במחלקה שלו
    if current_user['role'] == 'ממ' and current_user['mahlaka_id'] == mahlaka_id:
        return True
    
    # מ"כ יכול לערוך את הכיתה שלו
    if current_user['role'] == 'מכ' and current_user['kita'] == kita_name and \
       current_user['mahlaka_id'] == mahlaka_id:
        return True
    
    return False


def can_create_shavzak(current_user):
    """בדיקה האם המשתמש יכול ליצור שיבוץ"""
    # רק מ"פ ומ"מ יכולים ליצור שיבוצים
    return current_user['role'] in ['מפ', 'ממ']


def can_view_shavzak(current_user, shavzak_pluga_id):
    """בדיקה האם המשתמש יכול לצפות בשיבוץ"""
    # כולם בפלוגה יכולים לצפות
    return current_user['pluga_id'] == shavzak_pluga_id


def get_accessible_mahalkot(current_user, session):
    """מחזיר רשימת מחלקות שהמשתמש יכול לגשת אליהן"""
    from models import Mahlaka
    
    if current_user['role'] == 'מפ':
        # מ"פ רואה את כל המחלקות בפלוגה
        return session.query(Mahlaka).filter_by(pluga_id=current_user['pluga_id']).all()
    
    elif current_user['role'] == 'ממ':
        # מ"מ רואה את המחלקה שלו
        return session.query(Mahlaka).filter_by(id=current_user['mahlaka_id']).all()
    
    elif current_user['role'] == 'מכ':
        # מ"כ רואה את המחלקה שלו (אבל יכול לערוך רק את הכיתה)
        return session.query(Mahlaka).filter_by(id=current_user['mahlaka_id']).all()
    
    return []


def get_accessible_soldiers(current_user, session):
    """מחזיר רשימת חיילים שהמשתמש יכול לגשת אליהם"""
    from models import Soldier, Mahlaka
    
    if current_user['role'] == 'מפ':
        # מ"פ רואה את כל החיילים בפלוגה
        mahalkot = session.query(Mahlaka).filter_by(pluga_id=current_user['pluga_id']).all()
        mahlaka_ids = [m.id for m in mahalkot]
        return session.query(Soldier).filter(Soldier.mahlaka_id.in_(mahlaka_ids)).all()
    
    elif current_user['role'] == 'ממ':
        # מ"מ רואה את כל החיילים במחלקה שלו
        return session.query(Soldier).filter_by(mahlaka_id=current_user['mahlaka_id']).all()
    
    elif current_user['role'] == 'מכ':
        # מ"כ רואה את החיילים בכיתה שלו
        return session.query(Soldier).filter_by(
            mahlaka_id=current_user['mahlaka_id'],
            kita=current_user['kita']
        ).all()
    
    return []
