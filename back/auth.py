"""
Authentication & Authorization System
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "your-secret-key-change-in-production"
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
    except:
        return None


def token_required(f):
    """דקורטור לבדיקת token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'פורמט token לא תקין'}), 401
        
        if not token:
            return jsonify({'error': 'חסר token'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Token לא תקף או פג תוקף'}), 401
        
        kwargs['current_user'] = payload
        return f(*args, **kwargs)
    
    return decorated


def role_required(allowed_roles):
    """דקורטור לבדיקת הרשאות"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                return jsonify({'error': 'נדרש אימות'}), 401
            
            if current_user.get('role') not in allowed_roles:
                return jsonify({'error': 'אין לך הרשאה לפעולה זו'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def can_edit_pluga(current_user, pluga_id):
    """בדיקה האם יכול לערוך פלוגה"""
    return current_user['role'] == 'מפ' and current_user['pluga_id'] == pluga_id


def can_view_pluga(current_user, pluga_id):
    """בדיקה האם יכול לצפות בפלוגה"""
    return current_user['pluga_id'] == pluga_id


def can_edit_mahlaka(current_user, mahlaka_id, session):
    """בדיקה האם יכול לערוך מחלקה"""
    from models import Mahlaka
    
    if current_user['role'] == 'מפ':
        mahlaka = session.query(Mahlaka).filter_by(id=mahlaka_id).first()
        if mahlaka and mahlaka.pluga_id == current_user['pluga_id']:
            return True
    
    if current_user['role'] == 'ממ' and current_user['mahlaka_id'] == mahlaka_id:
        return True
    
    return False


def can_view_mahlaka(current_user, mahlaka_id, session):
    """בדיקה האם יכול לצפות במחלקה"""
    from models import Mahlaka
    
    mahlaka = session.query(Mahlaka).filter_by(id=mahlaka_id).first()
    if not mahlaka:
        return False
    
    return mahlaka.pluga_id == current_user['pluga_id']


def can_edit_soldier(current_user, soldier_id, session):
    """בדיקה האם יכול לערוך חייל"""
    from models import Soldier, Mahlaka
    
    soldier = session.query(Soldier).filter_by(id=soldier_id).first()
    if not soldier:
        return False
    
    if current_user['role'] == 'מפ':
        mahlaka = session.query(Mahlaka).filter_by(id=soldier.mahlaka_id).first()
        if mahlaka and mahlaka.pluga_id == current_user['pluga_id']:
            return True
    
    if current_user['role'] == 'ממ' and soldier.mahlaka_id == current_user['mahlaka_id']:
        return True
    
    if current_user['role'] == 'מכ' and soldier.kita == current_user['kita'] and \
       soldier.mahlaka_id == current_user['mahlaka_id']:
        return True
    
    return False


def can_create_shavzak(current_user):
    """בדיקה האם יכול ליצור שיבוץ"""
    return current_user['role'] in ['מפ', 'ממ']


def can_view_shavzak(current_user, shavzak_pluga_id):
    """בדיקה האם יכול לצפות בשיבוץ"""
    return current_user['pluga_id'] == shavzak_pluga_id
