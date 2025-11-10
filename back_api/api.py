"""
Shavzak API Server
מערכת ניהול שיבוצים צבאית
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from sqlalchemy import func
import traceback

from models import (
    init_db, get_session, User, Pluga, Mahlaka, Soldier, 
    Certification, UnavailableDate, AssignmentTemplate, 
    Shavzak, Assignment, AssignmentSoldier
)
from auth import (
    create_token, token_required, role_required,
    can_edit_pluga, can_view_pluga, can_edit_mahlaka, can_view_mahlaka,
    can_edit_soldier, can_create_shavzak, can_view_shavzak,
    get_accessible_mahalkot, get_accessible_soldiers, can_edit_kita
)

app = Flask(__name__)
CORS(app)

# Initialize database
engine = init_db()

# Helper function
def get_db():
    """מקבל session של DB"""
    return get_session(engine)


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/register', methods=['POST'])
def register():
    """רישום משתמש ראשוני - רק למ"פ בהתחלה"""
    try:
        data = request.json
        session = get_db()
        
        # בדיקה אם כבר יש משתמשים (אם כן, רק מ"פ יכול להוסיף)
        existing_users = session.query(User).count()
        if existing_users > 0:
            return jsonify({'error': 'לא ניתן להירשם ישירות. צור קשר עם מ"פ'}), 403
        
        # יצירת משתמש ראשון (מ"פ)
        user = User(
            username=data['username'],
            full_name=data['full_name'],
            role='מפ'
        )
        user.set_password(data['password'])
        
        session.add(user)
        session.commit()
        
        token = create_token(user)
        
        return jsonify({
            'message': 'משתמש נוצר בהצלחה',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/login', methods=['POST'])
def login():
    """התחברות"""
    try:
        data = request.json
        session = get_db()
        
        user = session.query(User).filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'שם משתמש או סיסמה שגויים'}), 401
        
        # עדכון זמן התחברות אחרון
        user.last_login = datetime.utcnow()
        session.commit()
        
        token = create_token(user)
        
        return jsonify({
            'message': 'התחברת בהצלחה',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'pluga_id': user.pluga_id,
                'mahlaka_id': user.mahlaka_id,
                'kita': user.kita
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/users', methods=['POST'])
@token_required
@role_required(['מפ', 'ממ'])
def create_user(current_user):
    """יצירת משתמש חדש - רק מ"פ ומ"מ"""
    try:
        data = request.json
        session = get_db()
        
        # מ"פ יכול ליצור כל סוג משתמש
        # מ"מ יכול ליצור רק מ"כ במחלקה שלו
        if current_user['role'] == 'ממ':
            if data['role'] != 'מכ' or data.get('mahlaka_id') != current_user['mahlaka_id']:
                return jsonify({'error': 'מ"מ יכול ליצור רק מ"כ במחלקה שלו'}), 403
        
        user = User(
            username=data['username'],
            full_name=data['full_name'],
            role=data['role'],
            pluga_id=data.get('pluga_id'),
            mahlaka_id=data.get('mahlaka_id'),
            kita=data.get('kita')
        )
        user.set_password(data['password'])
        
        session.add(user)
        session.commit()
        
        return jsonify({
            'message': 'משתמש נוצר בהצלחה',
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# PLUGA ENDPOINTS
# ============================================================================

@app.route('/api/plugot', methods=['POST'])
@token_required
@role_required(['מפ'])
def create_pluga(current_user):
    """יצירת פלוגה - רק מ"פ ללא פלוגה"""
    try:
        data = request.json
        session = get_db()
        
        # בדיקה שהמשתמש עדיין לא משויך לפלוגה
        user = session.query(User).filter_by(id=current_user['user_id']).first()
        if user.pluga_id:
            return jsonify({'error': 'אתה כבר משויך לפלוגה'}), 400
        
        pluga = Pluga(
            name=data['name'],
            gdud=data.get('gdud', ''),
            color=data.get('color', '#FFFFFF')
        )
        
        session.add(pluga)
        session.flush()  # כדי לקבל את ה-ID
        
        # עדכון המשתמש
        user.pluga_id = pluga.id
        session.commit()
        
        return jsonify({
            'message': 'פלוגה נוצרה בהצלחה',
            'pluga': {
                'id': pluga.id,
                'name': pluga.name,
                'gdud': pluga.gdud,
                'color': pluga.color
            }
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/plugot/<int:pluga_id>', methods=['GET'])
@token_required
def get_pluga(pluga_id, current_user):
    """קבלת פרטי פלוגה"""
    try:
        session = get_db()
        
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה לצפות בפלוגה זו'}), 403
        
        pluga = session.query(Pluga).filter_by(id=pluga_id).first()
        if not pluga:
            return jsonify({'error': 'פלוגה לא נמצאה'}), 404
        
        mahalkot = session.query(Mahlaka).filter_by(pluga_id=pluga_id).all()
        
        return jsonify({
            'pluga': {
                'id': pluga.id,
                'name': pluga.name,
                'gdud': pluga.gdud,
                'color': pluga.color,
                'mahalkot_count': len(mahalkot)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/plugot/<int:pluga_id>', methods=['PUT'])
@token_required
def update_pluga(pluga_id, current_user):
    """עדכון פרטי פלוגה"""
    try:
        session = get_db()
        
        if not can_edit_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה לערוך פלוגה זו'}), 403
        
        pluga = session.query(Pluga).filter_by(id=pluga_id).first()
        if not pluga:
            return jsonify({'error': 'פלוגה לא נמצאה'}), 404
        
        data = request.json
        if 'name' in data:
            pluga.name = data['name']
        if 'gdud' in data:
            pluga.gdud = data['gdud']
        if 'color' in data:
            pluga.color = data['color']
        
        session.commit()
        
        return jsonify({'message': 'פלוגה עודכנה בהצלחה'}), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# MAHLAKA ENDPOINTS
# ============================================================================

@app.route('/api/mahalkot', methods=['POST'])
@token_required
@role_required(['מפ'])
def create_mahlaka(current_user):
    """יצירת מחלקה - רק מ"פ"""
    try:
        data = request.json
        session = get_db()
        
        pluga_id = data.get('pluga_id', current_user['pluga_id'])
        
        if not can_edit_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה ליצור מחלקה בפלוגה זו'}), 403
        
        mahlaka = Mahlaka(
            number=data['number'],
            color=data.get('color', '#FFFFFF'),
            pluga_id=pluga_id
        )
        
        session.add(mahlaka)
        session.commit()
        
        return jsonify({
            'message': 'מחלקה נוצרה בהצלחה',
            'mahlaka': {
                'id': mahlaka.id,
                'number': mahlaka.number,
                'color': mahlaka.color
            }
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/mahalkot/<int:mahlaka_id>', methods=['GET'])
@token_required
def get_mahlaka(mahlaka_id, current_user):
    """קבלת פרטי מחלקה"""
    try:
        session = get_db()
        
        if not can_view_mahlaka(current_user, mahlaka_id, session):
            return jsonify({'error': 'אין לך הרשאה לצפות במחלקה זו'}), 403
        
        mahlaka = session.query(Mahlaka).filter_by(id=mahlaka_id).first()
        if not mahlaka:
            return jsonify({'error': 'מחלקה לא נמצאה'}), 404
        
        soldiers = session.query(Soldier).filter_by(mahlaka_id=mahlaka_id).all()
        
        # חלוקה לפי תפקידים
        commanders = [s for s in soldiers if s.role in ['ממ', 'מכ', 'סמל']]
        drivers = [s for s in soldiers if s.role == 'נהג']
        regular_soldiers = [s for s in soldiers if s.role == 'לוחם']
        
        return jsonify({
            'mahlaka': {
                'id': mahlaka.id,
                'number': mahlaka.number,
                'color': mahlaka.color,
                'pluga_id': mahlaka.pluga_id,
                'stats': {
                    'total_soldiers': len(soldiers),
                    'commanders': len(commanders),
                    'drivers': len(drivers),
                    'soldiers': len(regular_soldiers)
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/plugot/<int:pluga_id>/mahalkot', methods=['GET'])
@token_required
def list_mahalkot(pluga_id, current_user):
    """רשימת מחלקות בפלוגה"""
    try:
        session = get_db()
        
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה לצפות בפלוגה זו'}), 403
        
        mahalkot = session.query(Mahlaka).filter_by(pluga_id=pluga_id).all()
        
        result = []
        for mahlaka in mahalkot:
            soldiers_count = session.query(Soldier).filter_by(mahlaka_id=mahlaka.id).count()
            result.append({
                'id': mahlaka.id,
                'number': mahlaka.number,
                'color': mahlaka.color,
                'soldiers_count': soldiers_count
            })
        
        return jsonify({'mahalkot': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# SOLDIER ENDPOINTS
# ============================================================================

@app.route('/api/soldiers', methods=['POST'])
@token_required
def create_soldier(current_user):
    """יצירת חייל"""
    try:
        data = request.json
        session = get_db()
        
        mahlaka_id = data['mahlaka_id']
        
        if not can_edit_mahlaka(current_user, mahlaka_id, session):
            return jsonify({'error': 'אין לך הרשאה להוסיף חייל למחלקה זו'}), 403
        
        # אם זה מ"כ, לוודא שהחייל בכיתה שלו
        if current_user['role'] == 'מכ':
            if data.get('kita') != current_user['kita']:
                return jsonify({'error': 'אתה יכול להוסיף חיילים רק לכיתה שלך'}), 403
        
        soldier = Soldier(
            name=data['name'],
            role=data['role'],
            mahlaka_id=mahlaka_id,
            kita=data.get('kita'),
            idf_id=data.get('idf_id'),
            personal_id=data.get('personal_id'),
            sex=data.get('sex'),
            phone_number=data.get('phone_number'),
            address=data.get('address'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_number=data.get('emergency_contact_number'),
            pakal=data.get('pakal'),
            is_platoon_commander=data.get('is_platoon_commander', False),
            has_hatashab=data.get('has_hatashab', False)
        )
        
        # תאריכים
        if data.get('recruit_date'):
            soldier.recruit_date = datetime.strptime(data['recruit_date'], '%Y-%m-%d').date()
        if data.get('birth_date'):
            soldier.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        if data.get('home_round_date'):
            soldier.home_round_date = datetime.strptime(data['home_round_date'], '%Y-%m-%d').date()
        
        session.add(soldier)
        session.flush()
        
        # הוספת הסמכות
        if 'certifications' in data:
            for cert_name in data['certifications']:
                cert = Certification(soldier_id=soldier.id, certification_name=cert_name)
                session.add(cert)
        
        session.commit()
        
        return jsonify({
            'message': 'חייל נוסף בהצלחה',
            'soldier': {
                'id': soldier.id,
                'name': soldier.name,
                'role': soldier.role,
                'kita': soldier.kita
            }
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/soldiers/<int:soldier_id>', methods=['GET'])
@token_required
def get_soldier(soldier_id, current_user):
    """קבלת פרטי חייל"""
    try:
        session = get_db()
        
        soldier = session.query(Soldier).filter_by(id=soldier_id).first()
        if not soldier:
            return jsonify({'error': 'חייל לא נמצא'}), 404
        
        if not can_view_mahlaka(current_user, soldier.mahlaka_id, session):
            return jsonify({'error': 'אין לך הרשאה לצפות בחייל זה'}), 403
        
        # הסמכות
        certifications = session.query(Certification).filter_by(soldier_id=soldier_id).all()
        cert_list = [cert.certification_name for cert in certifications]
        
        # תאריכים לא זמינים
        unavailable = session.query(UnavailableDate).filter_by(soldier_id=soldier_id).all()
        unavailable_list = [{
            'id': u.id,
            'date': u.date.isoformat(),
            'reason': u.reason,
            'status': u.status
        } for u in unavailable]
        
        return jsonify({
            'soldier': {
                'id': soldier.id,
                'name': soldier.name,
                'role': soldier.role,
                'kita': soldier.kita,
                'idf_id': soldier.idf_id,
                'personal_id': soldier.personal_id,
                'sex': soldier.sex,
                'phone_number': soldier.phone_number,
                'address': soldier.address,
                'emergency_contact_name': soldier.emergency_contact_name,
                'emergency_contact_number': soldier.emergency_contact_number,
                'pakal': soldier.pakal,
                'recruit_date': soldier.recruit_date.isoformat() if soldier.recruit_date else None,
                'birth_date': soldier.birth_date.isoformat() if soldier.birth_date else None,
                'home_round_date': soldier.home_round_date.isoformat() if soldier.home_round_date else None,
                'is_platoon_commander': soldier.is_platoon_commander,
                'has_hatashab': soldier.has_hatashab,
                'mahlaka_id': soldier.mahlaka_id,
                'certifications': cert_list,
                'unavailable_dates': unavailable_list
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/soldiers/<int:soldier_id>', methods=['PUT'])
@token_required
def update_soldier(soldier_id, current_user):
    """עדכון פרטי חייל"""
    try:
        session = get_db()
        
        if not can_edit_soldier(current_user, soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה לערוך חייל זה'}), 403
        
        soldier = session.query(Soldier).filter_by(id=soldier_id).first()
        if not soldier:
            return jsonify({'error': 'חייל לא נמצא'}), 404
        
        data = request.json
        
        # עדכון שדות בסיסיים
        updatable_fields = [
            'name', 'role', 'kita', 'idf_id', 'personal_id', 'sex',
            'phone_number', 'address', 'emergency_contact_name',
            'emergency_contact_number', 'pakal', 'is_platoon_commander', 'has_hatashab'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(soldier, field, data[field])
        
        # עדכון תאריכים
        if 'recruit_date' in data and data['recruit_date']:
            soldier.recruit_date = datetime.strptime(data['recruit_date'], '%Y-%m-%d').date()
        if 'birth_date' in data and data['birth_date']:
            soldier.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        if 'home_round_date' in data and data['home_round_date']:
            soldier.home_round_date = datetime.strptime(data['home_round_date'], '%Y-%m-%d').date()
        
        session.commit()
        
        return jsonify({'message': 'חייל עודכן בהצלחה'}), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/soldiers/<int:soldier_id>', methods=['DELETE'])
@token_required
def delete_soldier(soldier_id, current_user):
    """מחיקת חייל"""
    try:
        session = get_db()
        
        if not can_edit_soldier(current_user, soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה למחוק חייל זה'}), 403
        
        soldier = session.query(Soldier).filter_by(id=soldier_id).first()
        if not soldier:
            return jsonify({'error': 'חייל לא נמצא'}), 404
        
        session.delete(soldier)
        session.commit()
        
        return jsonify({'message': 'חייל נמחק בהצלחה'}), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/mahalkot/<int:mahlaka_id>/soldiers', methods=['GET'])
@token_required
def list_soldiers_by_mahlaka(mahlaka_id, current_user):
    """רשימת חיילים במחלקה"""
    try:
        session = get_db()
        
        if not can_view_mahlaka(current_user, mahlaka_id, session):
            return jsonify({'error': 'אין לך הרשאה לצפות במחלקה זו'}), 403
        
        soldiers = session.query(Soldier).filter_by(mahlaka_id=mahlaka_id).all()
        
        # אם זה מ"כ, להציג רק את החיילים בכיתה שלו
        if current_user['role'] == 'מכ':
            soldiers = [s for s in soldiers if s.kita == current_user['kita']]
        
        result = []
        for soldier in soldiers:
            certifications = session.query(Certification).filter_by(soldier_id=soldier.id).all()
            cert_list = [cert.certification_name for cert in certifications]
            
            result.append({
                'id': soldier.id,
                'name': soldier.name,
                'role': soldier.role,
                'kita': soldier.kita,
                'certifications': cert_list,
                'is_platoon_commander': soldier.is_platoon_commander,
                'has_hatashab': soldier.has_hatashab
            })
        
        return jsonify({'soldiers': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# CERTIFICATIONS & UNAVAILABILITY
# ============================================================================

@app.route('/api/soldiers/<int:soldier_id>/certifications', methods=['POST'])
@token_required
def add_certification(soldier_id, current_user):
    """הוספת הסמכה לחייל"""
    try:
        session = get_db()
        
        if not can_edit_soldier(current_user, soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה לערוך חייל זה'}), 403
        
        data = request.json
        cert = Certification(
            soldier_id=soldier_id,
            certification_name=data['certification_name']
        )
        
        session.add(cert)
        session.commit()
        
        return jsonify({'message': 'הסמכה נוספה בהצלחה'}), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/soldiers/<int:soldier_id>/unavailable', methods=['POST'])
@token_required
def add_unavailable_date(soldier_id, current_user):
    """הוספת תאריך שבו חייל לא זמין"""
    try:
        session = get_db()
        
        if not can_edit_soldier(current_user, soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה לערוך חייל זה'}), 403
        
        data = request.json
        unavailable = UnavailableDate(
            soldier_id=soldier_id,
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            reason=data.get('reason', ''),
            status=data.get('status', 'approved')
        )
        
        session.add(unavailable)
        session.commit()
        
        return jsonify({'message': 'תאריך נוסף בהצלחה'}), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/unavailable/<int:unavailable_id>', methods=['DELETE'])
@token_required
def delete_unavailable_date(unavailable_id, current_user):
    """מחיקת תאריך לא זמין"""
    try:
        session = get_db()
        
        unavailable = session.query(UnavailableDate).filter_by(id=unavailable_id).first()
        if not unavailable:
            return jsonify({'error': 'רשומה לא נמצאה'}), 404
        
        if not can_edit_soldier(current_user, unavailable.soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        session.delete(unavailable)
        session.commit()
        
        return jsonify({'message': 'תאריך נמחק בהצלחה'}), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# ASSIGNMENT TEMPLATES
# ============================================================================

@app.route('/api/plugot/<int:pluga_id>/assignment-templates', methods=['POST'])
@token_required
@role_required(['מפ'])
def create_assignment_template(pluga_id, current_user):
    """יצירת תבנית משימה"""
    try:
        session = get_db()
        
        if not can_edit_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        data = request.json
        template = AssignmentTemplate(
            pluga_id=pluga_id,
            name=data['name'],
            assignment_type=data['assignment_type'],
            length_in_hours=data['length_in_hours'],
            times_per_day=data['times_per_day'],
            commanders_needed=data.get('commanders_needed', 0),
            drivers_needed=data.get('drivers_needed', 0),
            soldiers_needed=data.get('soldiers_needed', 0),
            same_mahlaka_required=data.get('same_mahlaka_required', False),
            requires_certification=data.get('requires_certification'),
            requires_senior_commander=data.get('requires_senior_commander', False)
        )
        
        session.add(template)
        session.commit()
        
        return jsonify({
            'message': 'תבנית נוצרה בהצלחה',
            'template': {
                'id': template.id,
                'name': template.name,
                'assignment_type': template.assignment_type
            }
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/plugot/<int:pluga_id>/assignment-templates', methods=['GET'])
@token_required
def list_assignment_templates(pluga_id, current_user):
    """רשימת תבניות משימות"""
    try:
        session = get_db()
        
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        templates = session.query(AssignmentTemplate).filter_by(pluga_id=pluga_id).all()
        
        result = [{
            'id': t.id,
            'name': t.name,
            'assignment_type': t.assignment_type,
            'length_in_hours': t.length_in_hours,
            'times_per_day': t.times_per_day,
            'commanders_needed': t.commanders_needed,
            'drivers_needed': t.drivers_needed,
            'soldiers_needed': t.soldiers_needed,
            'same_mahlaka_required': t.same_mahlaka_required,
            'requires_certification': t.requires_certification,
            'requires_senior_commander': t.requires_senior_commander
        } for t in templates]
        
        return jsonify({'templates': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# SHAVZAK (SCHEDULING) ENDPOINTS
# ============================================================================

@app.route('/api/shavzakim', methods=['POST'])
@token_required
def create_shavzak(current_user):
    """יצירת שיבוץ חדש"""
    try:
        if not can_create_shavzak(current_user):
            return jsonify({'error': 'אין לך הרשאה ליצור שיבוץ'}), 403
        
        data = request.json
        session = get_db()
        
        pluga_id = data.get('pluga_id', current_user['pluga_id'])
        
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        shavzak = Shavzak(
            pluga_id=pluga_id,
            name=data['name'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            days_count=data['days_count'],
            created_by=current_user['user_id'],
            min_rest_hours=data.get('min_rest_hours', 8),
            emergency_mode=data.get('emergency_mode', False)
        )
        
        session.add(shavzak)
        session.commit()
        
        return jsonify({
            'message': 'שיבוץ נוצר בהצלחה',
            'shavzak': {
                'id': shavzak.id,
                'name': shavzak.name,
                'start_date': shavzak.start_date.isoformat(),
                'days_count': shavzak.days_count
            }
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/shavzakim/<int:shavzak_id>/generate', methods=['POST'])
@token_required
def generate_shavzak(shavzak_id, current_user):
    """הרצת אלגוריתם השיבוץ"""
    try:
        session = get_db()
        
        shavzak = session.query(Shavzak).filter_by(id=shavzak_id).first()
        if not shavzak:
            return jsonify({'error': 'שיבוץ לא נמצא'}), 404
        
        if not can_view_shavzak(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        # TODO: להריץ את אלגוריתם השיבוץ המלא כאן
        # כרגע זה placeholder
        
        return jsonify({
            'message': 'שיבוץ בוצע בהצלחה',
            'warnings': [],
            'stats': {
                'total_assignments': 0,
                'emergency_assignments': 0
            }
        }), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/shavzakim/<int:shavzak_id>', methods=['GET'])
@token_required
def get_shavzak(shavzak_id, current_user):
    """קבלת פרטי שיבוץ"""
    try:
        session = get_db()
        
        shavzak = session.query(Shavzak).filter_by(id=shavzak_id).first()
        if not shavzak:
            return jsonify({'error': 'שיבוץ לא נמצא'}), 404
        
        if not can_view_shavzak(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        assignments = session.query(Assignment).filter_by(shavzak_id=shavzak_id).all()
        
        assignments_data = []
        for assign in assignments:
            soldiers = session.query(AssignmentSoldier, Soldier).join(
                Soldier, AssignmentSoldier.soldier_id == Soldier.id
            ).filter(AssignmentSoldier.assignment_id == assign.id).all()
            
            soldiers_list = [{
                'id': s.Soldier.id,
                'name': s.Soldier.name,
                'role': s.AssignmentSoldier.role_in_assignment
            } for s in soldiers]
            
            assignments_data.append({
                'id': assign.id,
                'name': assign.name,
                'type': assign.assignment_type,
                'day': assign.day,
                'start_hour': assign.start_hour,
                'length_in_hours': assign.length_in_hours,
                'assigned_mahlaka_id': assign.assigned_mahlaka_id,
                'soldiers': soldiers_list
            })
        
        return jsonify({
            'shavzak': {
                'id': shavzak.id,
                'name': shavzak.name,
                'start_date': shavzak.start_date.isoformat(),
                'days_count': shavzak.days_count,
                'created_at': shavzak.created_at.isoformat(),
                'min_rest_hours': shavzak.min_rest_hours,
                'emergency_mode': shavzak.emergency_mode
            },
            'assignments': assignments_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/plugot/<int:pluga_id>/shavzakim', methods=['GET'])
@token_required
def list_shavzakim(pluga_id, current_user):
    """רשימת שיבוצים של פלוגה"""
    try:
        session = get_db()
        
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        shavzakim = session.query(Shavzak).filter_by(pluga_id=pluga_id).order_by(
            Shavzak.created_at.desc()
        ).all()
        
        result = [{
            'id': s.id,
            'name': s.name,
            'start_date': s.start_date.isoformat(),
            'days_count': s.days_count,
            'created_at': s.created_at.isoformat()
        } for s in shavzakim]
        
        return jsonify({'shavzakim': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.route('/api/me', methods=['GET'])
@token_required
def get_current_user_info(current_user):
    """מידע על המשתמש המחובר"""
    try:
        session = get_db()
        
        user = session.query(User).filter_by(id=current_user['user_id']).first()
        if not user:
            return jsonify({'error': 'משתמש לא נמצא'}), 404
        
        pluga = None
        if user.pluga_id:
            pluga = session.query(Pluga).filter_by(id=user.pluga_id).first()
        
        mahlaka = None
        if user.mahlaka_id:
            mahlaka = session.query(Mahlaka).filter_by(id=user.mahlaka_id).first()
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'pluga': {
                    'id': pluga.id,
                    'name': pluga.name
                } if pluga else None,
                'mahlaka': {
                    'id': mahlaka.id,
                    'number': mahlaka.number
                } if mahlaka else None,
                'kita': user.kita,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    """סטטיסטיקות כלליות"""
    try:
        session = get_db()
        
        pluga_id = current_user['pluga_id']
        
        if not pluga_id:
            return jsonify({'error': 'אין פלוגה משויכת'}), 400
        
        # ספירת מחלקות
        mahalkot_count = session.query(Mahlaka).filter_by(pluga_id=pluga_id).count()
        
        # ספירת חיילים
        mahalkot = session.query(Mahlaka).filter_by(pluga_id=pluga_id).all()
        mahlaka_ids = [m.id for m in mahalkot]
        
        total_soldiers = session.query(Soldier).filter(Soldier.mahlaka_id.in_(mahlaka_ids)).count()
        commanders = session.query(Soldier).filter(
            Soldier.mahlaka_id.in_(mahlaka_ids),
            Soldier.role.in_(['ממ', 'מכ', 'סמל'])
        ).count()
        drivers = session.query(Soldier).filter(
            Soldier.mahlaka_id.in_(mahlaka_ids),
            Soldier.role == 'נהג'
        ).count()
        soldiers = session.query(Soldier).filter(
            Soldier.mahlaka_id.in_(mahlaka_ids),
            Soldier.role == 'לוחם'
        ).count()
        
        # ספירת שיבוצים
        shavzakim_count = session.query(Shavzak).filter_by(pluga_id=pluga_id).count()
        
        return jsonify({
            'stats': {
                'mahalkot': mahalkot_count,
                'total_soldiers': total_soldiers,
                'commanders': commanders,
                'drivers': drivers,
                'soldiers': soldiers,
                'shavzakim': shavzakim_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/health', methods=['GET'])
def health_check():
    """בדיקת תקינות השרת"""
    return jsonify({
        'status': 'healthy',
        'message': 'Shavzak API is running'
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'נתיב לא נמצא'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'שגיאת שרת פנימית'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("🎖️  Shavzak API Server Starting...")
    print("=" * 70)
    print("📋 Database initialized")
    print("🔐 Authentication enabled")
    print("🚀 Server running on http://localhost:5000")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
