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
    Shavzak, Assignment, AssignmentSoldier, JoinRequest,
    SchedulingConstraint
)
from auth import (
    create_token, token_required, role_required,
    can_edit_pluga, can_view_pluga, can_edit_mahlaka, can_view_mahlaka,
    can_edit_soldier, can_create_shavzak, can_view_shavzak
)
from assignment_logic import AssignmentLogic
import os
import sqlite3

app = Flask(__name__)
CORS(app)

# ודא שה-DB נמצא תמיד באותו מיקום (תיקיית back)
DB_PATH = os.path.join(os.path.dirname(__file__), 'shavzak.db')
engine = init_db(DB_PATH)

def check_and_run_migrations():
    """בדיקה והרצת migrations אוטומטית בעת אתחול"""
    try:
        if not os.path.exists(DB_PATH):
            print("⚠️  מסד הנתונים לא קיים - יש להריץ setup.py")
            return False

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # בדיקה 1: שדות חדשים ב-unavailable_dates
        cursor.execute("PRAGMA table_info(unavailable_dates)")
        unavailable_columns = [column[1] for column in cursor.fetchall()]

        missing_unavailable_columns = []
        required_unavailable_columns = ['end_date', 'unavailability_type', 'quantity']
        for col in required_unavailable_columns:
            if col not in unavailable_columns:
                missing_unavailable_columns.append(col)

        if missing_unavailable_columns:
            print(f"⚠️  מזהה שדות חסרים בטבלת unavailable_dates: {', '.join(missing_unavailable_columns)}")
            print("🔧 מריץ migration אוטומטי...")
            conn.close()
            from migrate_unavailable_dates import migrate_database
            if migrate_database(DB_PATH):
                print("✅ Migration לטבלת unavailable_dates הושלם בהצלחה")
            else:
                print("❌ Migration לטבלת unavailable_dates נכשל")
                return False
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

        # בדיקה 2: הסרת is_platoon_commander מטבלת soldiers
        cursor.execute("PRAGMA table_info(soldiers)")
        soldier_columns = [column[1] for column in cursor.fetchall()]

        if 'is_platoon_commander' in soldier_columns:
            print("⚠️  מזהה עמודה מיותרת: is_platoon_commander")
            print("🔧 מריץ migration אוטומטי להסרת is_platoon_commander...")
            conn.close()
            from migrate_remove_platoon_commander import migrate_database as migrate_remove_pc
            if migrate_remove_pc(DB_PATH):
                print("✅ Migration להסרת is_platoon_commander הושלם בהצלחה")
            else:
                print("❌ Migration להסרת is_platoon_commander נכשל")
                return False
        else:
            print("✅ is_platoon_commander כבר הוסר")

        conn.close()
        return True
    except Exception as e:
        print(f"⚠️  שגיאה בבדיקת schema: {e}")
        if 'conn' in locals():
            conn.close()
        return False

# הרצת migrations בעת אתחול
check_and_run_migrations()

def get_db():
    """מקבל session של DB"""
    return get_session(engine)


# ============================================================================
# AUTHENTICATION
# ============================================================================

@app.route('/api/register', methods=['POST'])
def register():
    """רישום משתמש חדש / בקשת הצטרפות"""
    try:
        data = request.json
        session = get_db()

        # בדיקה אם שם המשתמש כבר קיים
        existing_user = session.query(User).filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'error': 'שם המשתמש כבר קיים'}), 400

        # בדיקה אם שם המשתמש כבר קיים בבקשות ממתינות
        existing_request = session.query(JoinRequest).filter_by(
            username=data['username'],
            status='pending'
        ).first()
        if existing_request:
            return jsonify({'error': 'שם המשתמש כבר קיים בבקשה ממתינה'}), 400

        # אם אין משתמשים במערכת, המשתמש הראשון יהיה מפקד פלוגה
        existing_users_count = session.query(User).count()

        if existing_users_count == 0:
            # משתמש ראשון - יהיה מ"פ ראשי (יקבל אישור אוטומטי)
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
                    'role': user.role,
                    'pluga_id': user.pluga_id
                }
            }), 201
        else:
            # משתמשים נוספים (מפ חדש) - יוצרים בקשת הצטרפות
            # בודקים אם זה בקשת הצטרפות למפ (אין pluga_id)
            if 'pluga_id' not in data or not data.get('pluga_id'):
                # בקשת הצטרפות למפ חדש
                join_request = JoinRequest(
                    username=data['username'],
                    full_name=data['full_name'],
                    pluga_name=data.get('pluga_name', ''),
                    gdud=data.get('gdud', '')
                )
                join_request.set_password(data['password'])
                session.add(join_request)
                session.commit()

                return jsonify({
                    'message': 'בקשת ההצטרפות נשלחה בהצלחה. אנא המתן לאישור המפקד הראשי.',
                    'request_id': join_request.id
                }), 201
            else:
                # רישום רגיל למשתמש בפלוגה קיימת
                pluga = session.query(Pluga).filter_by(id=data['pluga_id']).first()
                if not pluga:
                    return jsonify({'error': 'פלוגה לא נמצאה'}), 404

                user = User(
                    username=data['username'],
                    full_name=data['full_name'],
                    role=data.get('role', 'חייל'),
                    pluga_id=data['pluga_id']
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
                        'role': user.role,
                        'pluga_id': user.pluga_id
                    }
                }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/mahalkot/<int:mahlaka_id>', methods=['DELETE'])
@token_required
def delete_mahlaka(mahlaka_id, current_user):
    """מחיקת מחלקה (עם בדיקות הרשאה)"""
    try:
        session = get_db()

        mahlaka = session.query(Mahlaka).filter_by(id=mahlaka_id).first()
        if not mahlaka:
            return jsonify({'error': 'מחלקה לא נמצאה'}), 404

        # Authorization
        if not can_edit_mahlaka(current_user, mahlaka_id, session):
            return jsonify({'error': 'אין לך הרשאה למחוק מחלקה זו'}), 403

        # Clear any users referencing this mahlaka
        users = session.query(User).filter_by(mahlaka_id=mahlaka_id).all()
        for u in users:
            u.mahlaka_id = None

        # Deleting mahlaka will cascade-delete soldiers due to model cascade
        session.delete(mahlaka)
        session.commit()

        return jsonify({'message': 'המחלקה נמחקה בהצלחה'}), 200
    except Exception as e:
        session.rollback()
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
        
        user.last_login = datetime.now()
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
    """יצירת משתמש"""
    try:
        data = request.json
        session = get_db()
        
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
# PLUGA
# ============================================================================

@app.route('/api/plugot', methods=['POST'])
@token_required
@role_required(['מפ'])
def create_pluga(current_user):
    """יצירת פלוגה"""
    try:
        data = request.json
        session = get_db()
        
        user = session.query(User).filter_by(id=current_user['user_id']).first()
        if user.pluga_id:
            return jsonify({'error': 'אתה כבר משויך לפלוגה'}), 400
        
        pluga = Pluga(
            name=data['name'],
            gdud=data.get('gdud', ''),
            color=data.get('color', '#FFFFFF')
        )
        
        session.add(pluga)
        session.flush()
        
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


@app.route('/api/plugot', methods=['GET'])
def list_all_plugot():
    """קבלת רשימת כל הפלוגות (ללא אימות - לצורך רישום)"""
    try:
        session = get_db()
        plugot = session.query(Pluga).all()

        result = [{
            'id': p.id,
            'name': p.name,
            'gdud': p.gdud
        } for p in plugot]

        return jsonify({'plugot': result}), 200
    except Exception as e:
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
            return jsonify({'error': 'אין לך הרשאה'}), 403

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


# ============================================================================
# MAHLAKA
# ============================================================================

@app.route('/api/mahalkot', methods=['POST'])
@token_required
@role_required(['מפ'])
def create_mahlaka(current_user):
    """יצירת מחלקה"""
    try:
        data = request.json
        session = get_db()
        
        pluga_id = data.get('pluga_id', current_user['pluga_id'])
        
        if not can_edit_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
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


@app.route('/api/mahalkot/bulk', methods=['POST'])
@token_required
@role_required(['מפ'])
def create_mahalkot_bulk(current_user):
    """יצירת מחלקות בכמות גדולה (רשימה)"""
    try:
        data = request.json
        session = get_db()
        
        pluga_id = data.get('pluga_id', current_user['pluga_id'])
        
        if not can_edit_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        mahalkot_list = data.get('mahalkot', [])
        if not mahalkot_list:
            return jsonify({'error': 'רשימת מחלקות ריקה'}), 400
        
        created = []
        errors = []
        
        for idx, mahlaka_data in enumerate(mahalkot_list):
            try:
                # Validate required field
                if 'number' not in mahlaka_data:
                    errors.append(f"שורה {idx + 1}: חסר שדה 'number'")
                    continue
                
                # Check if mahlaka with this number already exists in pluga
                existing = session.query(Mahlaka).filter_by(
                    pluga_id=pluga_id,
                    number=mahlaka_data['number']
                ).first()
                
                if existing:
                    errors.append(f"שורה {idx + 1}: מחלקה {mahlaka_data['number']} כבר קיימת")
                    continue
                
                # Create mahlaka
                mahlaka = Mahlaka(
                    number=mahlaka_data['number'],
                    color=mahlaka_data.get('color', '#FFFFFF'),
                    pluga_id=pluga_id
                )
                
                session.add(mahlaka)
                session.flush()
                
                created.append({
                    'id': mahlaka.id,
                    'number': mahlaka.number,
                    'color': mahlaka.color
                })
            except Exception as e:
                errors.append(f"שורה {idx + 1}: {str(e)}")
        
        session.commit()
        
        return jsonify({
            'message': f'{len(created)} מחלקות נוצרו בהצלחה',
            'created': created,
            'errors': errors,
            'total': len(mahalkot_list),
            'success_count': len(created),
            'error_count': len(errors)
        }), 201 if created else 400
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/plugot/<int:pluga_id>/mahalkot', methods=['GET'])
@token_required
def list_mahalkot(pluga_id, current_user):
    """רשימת מחלקות"""
    try:
        session = get_db()
        
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
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
# SOLDIER
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
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
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
            has_hatashab=data.get('has_hatashab', False)
        )
        
        if data.get('recruit_date'):
            soldier.recruit_date = datetime.strptime(data['recruit_date'], '%Y-%m-%d').date()
        if data.get('birth_date'):
            soldier.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        if data.get('home_round_date'):
            soldier.home_round_date = datetime.strptime(data['home_round_date'], '%Y-%m-%d').date()
        
        session.add(soldier)
        session.flush()
        
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


@app.route('/api/soldiers/bulk', methods=['POST'])
@token_required
def create_soldiers_bulk(current_user):
    """יצירת חיילים בכמות גדולה (רשימה)"""
    try:
        data = request.json
        session = get_db()
        
        soldiers_list = data.get('soldiers', [])
        if not soldiers_list:
            return jsonify({'error': 'רשימת חיילים ריקה'}), 400
        
        created = []
        errors = []
        
        for idx, soldier_data in enumerate(soldiers_list):
            try:
                # Validate required fields
                if 'name' not in soldier_data:
                    errors.append(f"שורה {idx + 1}: חסר שדה 'name'")
                    continue
                if 'mahlaka_id' not in soldier_data:
                    errors.append(f"שורה {idx + 1}: חסר שדה 'mahlaka_id'")
                    continue
                if 'role' not in soldier_data:
                    errors.append(f"שורה {idx + 1}: חסר שדה 'role'")
                    continue
                
                mahlaka_id = soldier_data['mahlaka_id']
                
                # Authorization check
                if not can_edit_mahlaka(current_user, mahlaka_id, session):
                    errors.append(f"שורה {idx + 1}: אין לך הרשאה להוסיף לחיילים למחלקה זו")
                    continue
                
                # Role-based restrictions
                if current_user['role'] == 'מכ':
                    if soldier_data.get('kita') != current_user['kita']:
                        errors.append(f"שורה {idx + 1}: אתה יכול להוסיף חיילים רק לכיתה שלך")
                        continue
                
                # Create soldier
                soldier = Soldier(
                    name=soldier_data['name'],
                    role=soldier_data['role'],
                    mahlaka_id=mahlaka_id,
                    kita=soldier_data.get('kita'),
                    idf_id=soldier_data.get('idf_id'),
                    personal_id=soldier_data.get('personal_id'),
                    sex=soldier_data.get('sex'),
                    phone_number=soldier_data.get('phone_number'),
                    address=soldier_data.get('address'),
                    emergency_contact_name=soldier_data.get('emergency_contact_name'),
                    emergency_contact_number=soldier_data.get('emergency_contact_number'),
                    pakal=soldier_data.get('pakal'),
                    has_hatashab=soldier_data.get('has_hatashab', False)
                )
                
                # Parse dates if provided
                if soldier_data.get('recruit_date'):
                    try:
                        soldier.recruit_date = datetime.strptime(soldier_data['recruit_date'], '%Y-%m-%d').date()
                    except:
                        pass
                if soldier_data.get('birth_date'):
                    try:
                        soldier.birth_date = datetime.strptime(soldier_data['birth_date'], '%Y-%m-%d').date()
                    except:
                        pass
                if soldier_data.get('home_round_date'):
                    try:
                        soldier.home_round_date = datetime.strptime(soldier_data['home_round_date'], '%Y-%m-%d').date()
                    except:
                        pass
                
                session.add(soldier)
                session.flush()
                
                # Add unavailable_date if provided
                if soldier_data.get('unavailable_date'):
                    try:
                        # Parse DD.MM.YYYY format
                        date_str = soldier_data['unavailable_date'].strip()
                        unavailable = datetime.strptime(date_str, '%d.%m.%Y').date()
                        unavailable_record = UnavailableDate(soldier_id=soldier.id, date=unavailable)
                        session.add(unavailable_record)
                    except Exception as e:
                        # Silently fail if date parsing fails
                        pass
                
                # Add certifications if provided
                if 'certifications' in soldier_data:
                    for cert_name in soldier_data['certifications']:
                        cert = Certification(soldier_id=soldier.id, certification_name=cert_name)
                        session.add(cert)
                
                created.append({
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'kita': soldier.kita
                })
            except Exception as e:
                errors.append(f"שורה {idx + 1}: {str(e)}")
        
        session.commit()
        
        return jsonify({
            'message': f'{len(created)} חיילים נוצרו בהצלחה',
            'created': created,
            'errors': errors,
            'total': len(soldiers_list),
            'success_count': len(created),
            'error_count': len(errors)
        }), 201 if created else 400
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
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        certifications = session.query(Certification).filter_by(soldier_id=soldier_id).all()
        cert_list = [cert.certification_name for cert in certifications]
        
        unavailable = session.query(UnavailableDate).filter_by(soldier_id=soldier_id).all()
        unavailable_list = [{
            'id': u.id,
            'date': u.date.isoformat(),
            'end_date': u.end_date.isoformat() if hasattr(u, 'end_date') and u.end_date else None,
            'reason': u.reason,
            'status': u.status,
            'unavailability_type': u.unavailability_type if hasattr(u, 'unavailability_type') else 'חופשה',
            'quantity': u.quantity if hasattr(u, 'quantity') else None
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
            return jsonify({'error': 'אין לך הרשאה'}), 403

        soldier = session.query(Soldier).filter_by(id=soldier_id).first()
        if not soldier:
            return jsonify({'error': 'חייל לא נמצא'}), 404

        data = request.json

        # עדכון שדות בסיסיים (שדות חובה)
        if 'name' in data and data['name']:
            soldier.name = data['name']
        if 'role' in data and data['role']:
            soldier.role = data['role']
        if 'mahlaka_id' in data and data['mahlaka_id']:
            soldier.mahlaka_id = data['mahlaka_id']

        # עדכון שדות אופציונליים (רק אם יש ערך)
        if 'kita' in data and data['kita']:
            soldier.kita = data['kita']
        if 'idf_id' in data and data['idf_id']:
            soldier.idf_id = data['idf_id']
        if 'personal_id' in data and data['personal_id']:
            soldier.personal_id = data['personal_id']
        if 'sex' in data and data['sex']:
            soldier.sex = data['sex']
        if 'phone_number' in data and data['phone_number']:
            soldier.phone_number = data['phone_number']
        if 'address' in data and data['address']:
            soldier.address = data['address']
        if 'emergency_contact_name' in data and data['emergency_contact_name']:
            soldier.emergency_contact_name = data['emergency_contact_name']
        if 'emergency_contact_number' in data and data['emergency_contact_number']:
            soldier.emergency_contact_number = data['emergency_contact_number']
        if 'pakal' in data and data['pakal']:
            soldier.pakal = data['pakal']
        if 'has_hatash_2' in data:
            soldier.has_hatashab = data['has_hatash_2']
        if 'has_hatashab' in data:
            soldier.has_hatashab = data['has_hatashab']

        # עדכון תאריכים
        if 'recruit_date' in data and data['recruit_date']:
            soldier.recruit_date = datetime.strptime(data['recruit_date'], '%Y-%m-%d').date()
        if 'birth_date' in data and data['birth_date']:
            soldier.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        if 'home_round_date' in data and data['home_round_date']:
            soldier.home_round_date = datetime.strptime(data['home_round_date'], '%Y-%m-%d').date()

        session.commit()

        return jsonify({
            'message': 'חייל עודכן בהצלחה',
            'soldier': {
                'id': soldier.id,
                'name': soldier.name,
                'role': soldier.role,
                'kita': soldier.kita
            }
        }), 200
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
            return jsonify({'error': 'אין לך הרשאה'}), 403

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
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        soldiers = session.query(Soldier).filter_by(mahlaka_id=mahlaka_id).all()
        
        if current_user['role'] == 'מכ':
            soldiers = [s for s in soldiers if s.kita == current_user['kita']]
        
        result = []
        for soldier in soldiers:
            certifications = session.query(Certification).filter_by(soldier_id=soldier.id).all()
            cert_list = [cert.certification_name for cert in certifications]

            # קבל סטטוס נוכחי
            status = session.query(SoldierStatus).filter_by(soldier_id=soldier.id).first()

            # בדוק אם בסבב קו
            in_round = False
            if soldier.home_round_date:
                today = datetime.now().date()
                days_diff = (today - soldier.home_round_date).days
                cycle_position = days_diff % 21
                in_round = cycle_position < 4

            soldier_dict = {
                'id': soldier.id,
                'name': soldier.name,
                'role': soldier.role,
                'kita': soldier.kita,
                'certifications': cert_list,
                'has_hatashab': soldier.has_hatashab,
                'in_round': in_round
            }

            # הוסף סטטוס אם קיים
            if status:
                soldier_dict['status'] = {
                    'status_type': status.status_type,
                    'return_date': status.return_date.isoformat() if status.return_date else None,
                    'notes': status.notes
                }
            else:
                soldier_dict['status'] = None

            result.append(soldier_dict)

        return jsonify({'soldiers': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/soldiers/<int:soldier_id>/certifications', methods=['POST'])
@token_required
def add_certification(soldier_id, current_user):
    """הוספת הסמכה"""
    try:
        session = get_db()
        
        if not can_edit_soldier(current_user, soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
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
    """הוספת תאריך לא זמין"""
    try:
        session = get_db()

        if not can_edit_soldier(current_user, soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json
        start_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        unavailability_type = data.get('unavailability_type', 'חופשה')
        quantity = data.get('quantity')

        # חישוב תאריך סיום אוטומטי לגימלים וחק"צים
        end_date = None
        if unavailability_type in ['גימל', 'חק"צ', 'בקשת יציאה'] and quantity:
            # כל גימל/חק"צ/בקשת יציאה = 2 ימים
            # אם הזין את תאריך ההתחלה, נחשב את תאריך הסיום
            from datetime import timedelta
            end_date = start_date + timedelta(days=(quantity * 2) - 1)

        unavailable = UnavailableDate(
            soldier_id=soldier_id,
            date=start_date,
            end_date=end_date,
            reason=data.get('reason', ''),
            status=data.get('status', 'approved'),
            unavailability_type=unavailability_type,
            quantity=quantity
        )

        session.add(unavailable)
        session.flush()

        # מחק שיבוצים עתידיים שמושפעים מהחייל הזה
        soldier = session.query(Soldier).get(soldier_id)
        if soldier and soldier.mahlaka_id:
            mahlaka = session.query(Mahlaka).get(soldier.mahlaka_id)
            if mahlaka and mahlaka.pluga_id:
                # מצא את השיבוץ האוטומטי
                master_shavzak = session.query(Shavzak).filter(
                    Shavzak.pluga_id == mahlaka.pluga_id,
                    Shavzak.name == 'שיבוץ אוטומטי'
                ).first()

                if master_shavzak:
                    # חשב את הטווח של ימים שצריך למחוק
                    shavzak_start = master_shavzak.start_date
                    affected_start_day = (start_date - shavzak_start).days
                    affected_end_day = affected_start_day
                    if end_date:
                        affected_end_day = (end_date - shavzak_start).days

                    # מחק רק משימות שהחייל משובץ בהן בתאריכים המושפעים
                    for day in range(affected_start_day, affected_end_day + 1):
                        if day < 0:
                            continue
                        # מצא משימות שהחייל משובץ בהן ביום זה
                        soldier_assignments = session.query(AssignmentSoldier).join(Assignment).filter(
                            AssignmentSoldier.soldier_id == soldier_id,
                            Assignment.shavzak_id == master_shavzak.id,
                            Assignment.day == day
                        ).all()

                        # מחק את המשימות האלה (כל המשימה, לא רק השיוך של החייל)
                        for sa in soldier_assignments:
                            assignment = session.query(Assignment).get(sa.assignment_id)
                            if assignment:
                                # מחק את כל השיוכים של המשימה
                                session.query(AssignmentSoldier).filter(
                                    AssignmentSoldier.assignment_id == assignment.id
                                ).delete()
                                # מחק את המשימה עצמה
                                session.delete(assignment)

        session.commit()

        return jsonify({
            'message': 'תאריך נוסף בהצלחה',
            'unavailable_date': {
                'id': unavailable.id,
                'date': unavailable.date.isoformat(),
                'end_date': unavailable.end_date.isoformat() if unavailable.end_date else None,
                'reason': unavailable.reason,
                'status': unavailable.status,
                'unavailability_type': unavailable.unavailability_type,
                'quantity': unavailable.quantity
            }
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/unavailable/<int:unavailable_id>', methods=['DELETE'])
@token_required
def delete_unavailable_date(unavailable_id, current_user):
    """מחיקת תאריך אי זמינות"""
    try:
        session = get_db()

        unavailable = session.query(UnavailableDate).filter_by(id=unavailable_id).first()
        if not unavailable:
            return jsonify({'error': 'תאריך לא נמצא'}), 404

        if not can_edit_soldier(current_user, unavailable.soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        # שמור את הפרטים לפני המחיקה
        soldier_id = unavailable.soldier_id
        start_date = unavailable.date
        end_date = unavailable.end_date

        session.delete(unavailable)
        session.flush()

        # מחק שיבוצים עתידיים שמושפעים מהחייל הזה
        soldier = session.query(Soldier).get(soldier_id)
        if soldier and soldier.mahlaka_id:
            mahlaka = session.query(Mahlaka).get(soldier.mahlaka_id)
            if mahlaka and mahlaka.pluga_id:
                # מצא את השיבוץ האוטומטי
                master_shavzak = session.query(Shavzak).filter(
                    Shavzak.pluga_id == mahlaka.pluga_id,
                    Shavzak.name == 'שיבוץ אוטומטי'
                ).first()

                if master_shavzak:
                    # חשב את הטווח של ימים שצריך למחוק
                    shavzak_start = master_shavzak.start_date
                    affected_start_day = (start_date - shavzak_start).days
                    affected_end_day = affected_start_day
                    if end_date:
                        affected_end_day = (end_date - shavzak_start).days

                    # מחק משימות שהחייל משובץ בהן בתאריכים המושפעים
                    for day in range(affected_start_day, affected_end_day + 1):
                        if day < 0:
                            continue
                        # מצא משימות שהחייל משובץ בהן ביום זה
                        soldier_assignments = session.query(AssignmentSoldier).join(Assignment).filter(
                            AssignmentSoldier.soldier_id == soldier_id,
                            Assignment.shavzak_id == master_shavzak.id,
                            Assignment.day == day
                        ).all()

                        # מחק את המשימות האלה
                        for sa in soldier_assignments:
                            assignment = session.query(Assignment).get(sa.assignment_id)
                            if assignment:
                                session.query(AssignmentSoldier).filter(
                                    AssignmentSoldier.assignment_id == assignment.id
                                ).delete()
                                session.delete(assignment)

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
    """רשימת תבניות"""
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


@app.route('/api/assignment-templates/<int:template_id>', methods=['PUT'])
@token_required
@role_required(['מפ'])
def update_assignment_template(template_id, current_user):
    """עדכון תבנית משימה"""
    try:
        session = get_db()

        template = session.query(AssignmentTemplate).filter_by(id=template_id).first()
        if not template:
            return jsonify({'error': 'תבנית לא נמצאה'}), 404

        if not can_edit_pluga(current_user, template.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json

        if 'name' in data:
            template.name = data['name']
        if 'assignment_type' in data:
            template.assignment_type = data['assignment_type']
        if 'length_in_hours' in data:
            template.length_in_hours = data['length_in_hours']
        if 'times_per_day' in data:
            template.times_per_day = data['times_per_day']
        if 'commanders_needed' in data:
            template.commanders_needed = data['commanders_needed']
        if 'drivers_needed' in data:
            template.drivers_needed = data['drivers_needed']
        if 'soldiers_needed' in data:
            template.soldiers_needed = data['soldiers_needed']
        if 'same_mahlaka_required' in data:
            template.same_mahlaka_required = data['same_mahlaka_required']
        if 'requires_certification' in data:
            template.requires_certification = data['requires_certification']
        if 'requires_senior_commander' in data:
            template.requires_senior_commander = data['requires_senior_commander']

        session.commit()

        return jsonify({
            'message': 'תבנית עודכנה בהצלחה',
            'template': {
                'id': template.id,
                'name': template.name,
                'assignment_type': template.assignment_type
            }
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/assignment-templates/<int:template_id>', methods=['DELETE'])
@token_required
@role_required(['מפ'])
def delete_assignment_template(template_id, current_user):
    """מחיקת תבנית משימה"""
    try:
        session = get_db()

        template = session.query(AssignmentTemplate).filter_by(id=template_id).first()
        if not template:
            return jsonify({'error': 'תבנית לא נמצאה'}), 404

        if not can_edit_pluga(current_user, template.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        session.delete(template)
        session.commit()

        return jsonify({'message': 'תבנית נמחקה בהצלחה'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/assignment-templates/<int:template_id>/duplicate', methods=['POST'])
@token_required
@role_required(['מפ'])
def duplicate_assignment_template(template_id, current_user):
    """שכפול תבנית משימה"""
    try:
        session = get_db()

        # מציאת התבנית המקורית
        original_template = session.query(AssignmentTemplate).filter_by(id=template_id).first()
        if not original_template:
            return jsonify({'error': 'תבנית לא נמצאה'}), 404

        if not can_edit_pluga(current_user, original_template.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        # יצירת תבנית חדשה עם הנתונים של התבנית המקורית
        new_template = AssignmentTemplate(
            pluga_id=original_template.pluga_id,
            name=f"{original_template.name} (עותק)",
            assignment_type=original_template.assignment_type,
            length_in_hours=original_template.length_in_hours,
            times_per_day=original_template.times_per_day,
            commanders_needed=original_template.commanders_needed,
            drivers_needed=original_template.drivers_needed,
            soldiers_needed=original_template.soldiers_needed,
            same_mahlaka_required=original_template.same_mahlaka_required,
            requires_certification=original_template.requires_certification,
            requires_senior_commander=original_template.requires_senior_commander
        )

        session.add(new_template)
        session.commit()

        return jsonify({
            'message': 'תבנית שוכפלה בהצלחה',
            'template': {
                'id': new_template.id,
                'name': new_template.name,
                'assignment_type': new_template.assignment_type,
                'length_in_hours': new_template.length_in_hours,
                'times_per_day': new_template.times_per_day,
                'commanders_needed': new_template.commanders_needed,
                'drivers_needed': new_template.drivers_needed,
                'soldiers_needed': new_template.soldiers_needed,
                'same_mahlaka_required': new_template.same_mahlaka_required,
                'requires_certification': new_template.requires_certification,
                'requires_senior_commander': new_template.requires_senior_commander
            }
        }), 201
    except Exception as e:
        session.rollback()
        print(f"Error duplicating template: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# SHAVZAK (SCHEDULING)
# ============================================================================

@app.route('/api/shavzakim', methods=['POST'])
@token_required
def create_shavzak(current_user):
    """יצירת שיבוץ"""
    try:
        if not can_create_shavzak(current_user):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
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
    """הרצת אלגוריתם השיבוץ המלא"""
    try:
        session = get_db()
        
        shavzak = session.query(Shavzak).filter_by(id=shavzak_id).first()
        if not shavzak:
            return jsonify({'error': 'שיבוץ לא נמצא'}), 404
        
        if not can_view_shavzak(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403
        
        # מחיקת משימות קודמות
        session.query(Assignment).filter_by(shavzak_id=shavzak_id).delete()
        session.commit()
        
        # טעינת נתונים
        pluga = session.query(Pluga).filter_by(id=shavzak.pluga_id).first()
        mahalkot = session.query(Mahlaka).filter_by(pluga_id=pluga.id).all()
        templates = session.query(AssignmentTemplate).filter_by(pluga_id=pluga.id).all()
        
        if not templates:
            return jsonify({'error': 'לא קיימות תבניות משימות'}), 400
        
        # יצירת מבנה נתונים
        mahalkot_data = []
        for mahlaka in mahalkot:
            soldiers = session.query(Soldier).filter_by(mahlaka_id=mahlaka.id).all()
            
            commanders = []
            drivers = []
            regular_soldiers = []
            
            for soldier in soldiers:
                # בדיקת זמינות
                unavailable = session.query(UnavailableDate).filter(
                    UnavailableDate.soldier_id == soldier.id,
                    UnavailableDate.date >= shavzak.start_date,
                    UnavailableDate.date < shavzak.start_date + timedelta(days=shavzak.days_count)
                ).all()
                
                unavailable_dates = [u.date for u in unavailable]
                
                certifications = session.query(Certification).filter_by(soldier_id=soldier.id).all()
                cert_list = [c.certification_name for c in certifications]

                soldier_data = {
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'kita': soldier.kita,
                    'certifications': cert_list,
                    'unavailable_dates': unavailable_dates
                }

                if soldier.role in ['ממ', 'מכ', 'סמל']:
                    commanders.append(soldier_data)
                elif soldier.role == 'נהג':
                    drivers.append(soldier_data)
                else:
                    regular_soldiers.append(soldier_data)
            
            mahalkot_data.append({
                'id': mahlaka.id,
                'number': mahlaka.number,
                'commanders': commanders,
                'drivers': drivers,
                'soldiers': regular_soldiers
            })
        
        # אתחול אלגוריתם
        logic = AssignmentLogic(min_rest_hours=shavzak.min_rest_hours)
        
        # יצירת משימות
        all_assignments = []
        for day in range(shavzak.days_count):
            current_date = shavzak.start_date + timedelta(days=day)
            
            for template in templates:
                for slot in range(template.times_per_day):
                    start_hour = slot * template.length_in_hours
                    
                    assign_data = {
                        'name': f"{template.name} {slot + 1}",
                        'type': template.assignment_type,
                        'day': day,
                        'start_hour': start_hour,
                        'length_in_hours': template.length_in_hours,
                        'commanders_needed': template.commanders_needed,
                        'drivers_needed': template.drivers_needed,
                        'soldiers_needed': template.soldiers_needed,
                        'same_mahlaka_required': template.same_mahlaka_required,
                        'requires_certification': template.requires_certification,
                        'requires_senior_commander': template.requires_senior_commander,
                        'date': current_date
                    }
                    
                    all_assignments.append(assign_data)
        
        # מיון לפי יום ושעה
        all_assignments.sort(key=lambda x: (x['day'], x['start_hour']))
        
        # הרצת השיבוץ
        schedules = {}  # soldier_id -> [(day, start, end, name, type), ...]
        mahlaka_workload = {m['id']: 0 for m in mahalkot_data}
        
        all_commanders = [c for m in mahalkot_data for c in m['commanders']]
        all_drivers = [d for m in mahalkot_data for d in m['drivers']]
        all_soldiers = [s for m in mahalkot_data for s in m['soldiers']]
        
        failed_assignments = []
        
        for assign_data in all_assignments:
            try:
                # בדיקת זמינות לפי תאריך
                current_date = assign_data['date']
                
                # סינון חיילים לא זמינים
                available_mahalkot = []
                for mahlaka_info in mahalkot_data:
                    available_commanders = [
                        c for c in mahlaka_info['commanders']
                        if current_date not in c['unavailable_dates']
                    ]
                    available_drivers = [
                        d for d in mahlaka_info['drivers']
                        if current_date not in d['unavailable_dates']
                    ]
                    available_soldiers = [
                        s for s in mahlaka_info['soldiers']
                        if current_date not in s['unavailable_dates']
                    ]
                    
                    available_mahalkot.append({
                        'id': mahlaka_info['id'],
                        'number': mahlaka_info['number'],
                        'commanders': available_commanders,
                        'drivers': available_drivers,
                        'soldiers': available_soldiers
                    })
                
                available_commanders = [c for c in all_commanders if current_date not in c['unavailable_dates']]
                available_drivers = [d for d in all_drivers if current_date not in d['unavailable_dates']]
                available_soldiers = [s for s in all_soldiers if current_date not in s['unavailable_dates']]
                
                # בחירת פונקציית שיבוץ
                result = None
                if assign_data['type'] == 'סיור':
                    result = logic.assign_patrol(assign_data, available_mahalkot, schedules, mahlaka_workload)
                elif assign_data['type'] == 'שמירה':
                    result = logic.assign_guard(assign_data, available_soldiers, schedules)
                elif assign_data['type'] == 'כוננות א':
                    result = logic.assign_standby_a(assign_data, available_commanders, available_drivers, 
                                                    available_soldiers, schedules)
                elif assign_data['type'] == 'כוננות ב':
                    result = logic.assign_standby_b(assign_data, available_commanders, available_soldiers, schedules)
                elif assign_data['type'] == 'חמל':
                    result = logic.assign_operations(assign_data, available_commanders + available_soldiers, schedules)
                elif assign_data['type'] == 'תורן מטבח':
                    result = logic.assign_kitchen(assign_data, available_soldiers, schedules)
                elif assign_data['type'] == 'חפק גשש':
                    result = logic.assign_hafak_gashash(assign_data, available_commanders + available_soldiers, schedules)
                elif assign_data['type'] == 'שלז':
                    result = logic.assign_shalaz(assign_data, available_soldiers, schedules)
                elif assign_data['type'] == 'קצין תורן':
                    result = logic.assign_duty_officer(assign_data, available_commanders, schedules)
                else:
                    # ברירת מחדל - שמירה
                    result = logic.assign_guard(assign_data, available_soldiers, schedules)
                
                if result:
                    # שמירת משימה ב-DB
                    assignment = Assignment(
                        shavzak_id=shavzak_id,
                        name=assign_data['name'],
                        assignment_type=assign_data['type'],
                        day=assign_data['day'],
                        start_hour=assign_data['start_hour'],
                        length_in_hours=assign_data['length_in_hours'],
                        assigned_mahlaka_id=result.get('mahlaka_id')
                    )
                    session.add(assignment)
                    session.flush()
                    
                    # הוספת חיילים
                    for role_key in ['commanders', 'drivers', 'soldiers']:
                        if role_key in result:
                            role_name = role_key[:-1]  # הסרת 's'
                            for soldier_id in result[role_key]:
                                assign_soldier = AssignmentSoldier(
                                    assignment_id=assignment.id,
                                    soldier_id=soldier_id,
                                    role_in_assignment=role_name
                                )
                                session.add(assign_soldier)
                                
                                # עדכון schedules
                                if soldier_id not in schedules:
                                    schedules[soldier_id] = []
                                schedules[soldier_id].append((
                                    assign_data['day'],
                                    assign_data['start_hour'],
                                    assign_data['start_hour'] + assign_data['length_in_hours'],
                                    assign_data['name'],
                                    assign_data['type']
                                ))
                    
            except Exception as e:
                failed_assignments.append((assign_data, str(e)))
        
        # מצב חירום
        if failed_assignments:
            logic.enable_emergency_mode()
            
            for assign_data, error in failed_assignments:
                try:
                    current_date = assign_data['date']
                    
                    available_mahalkot = []
                    for mahlaka_info in mahalkot_data:
                        available_mahalkot.append({
                            'id': mahlaka_info['id'],
                            'number': mahlaka_info['number'],
                            'commanders': [c for c in mahlaka_info['commanders'] 
                                         if current_date not in c['unavailable_dates']],
                            'drivers': [d for d in mahlaka_info['drivers'] 
                                       if current_date not in d['unavailable_dates']],
                            'soldiers': [s for s in mahlaka_info['soldiers'] 
                                        if current_date not in s['unavailable_dates']]
                        })
                    
                    available_commanders = [c for c in all_commanders if current_date not in c['unavailable_dates']]
                    available_drivers = [d for d in all_drivers if current_date not in d['unavailable_dates']]
                    available_soldiers = [s for s in all_soldiers if current_date not in s['unavailable_dates']]
                    
                    result = None
                    if assign_data['type'] == 'סיור':
                        result = logic.assign_patrol(assign_data, available_mahalkot, schedules, mahlaka_workload)
                    elif assign_data['type'] == 'שמירה':
                        result = logic.assign_guard(assign_data, available_soldiers, schedules)
                    # ... (שאר הסוגים)
                    
                    if result:
                        assignment = Assignment(
                            shavzak_id=shavzak_id,
                            name=assign_data['name'],
                            assignment_type=assign_data['type'],
                            day=assign_data['day'],
                            start_hour=assign_data['start_hour'],
                            length_in_hours=assign_data['length_in_hours'],
                            assigned_mahlaka_id=result.get('mahlaka_id')
                        )
                        session.add(assignment)
                        session.flush()
                        
                        for role_key in ['commanders', 'drivers', 'soldiers']:
                            if role_key in result:
                                role_name = role_key[:-1]
                                for soldier_id in result[role_key]:
                                    assign_soldier = AssignmentSoldier(
                                        assignment_id=assignment.id,
                                        soldier_id=soldier_id,
                                        role_in_assignment=role_name
                                    )
                                    session.add(assign_soldier)
                                    
                                    if soldier_id not in schedules:
                                        schedules[soldier_id] = []
                                    schedules[soldier_id].append((
                                        assign_data['day'],
                                        assign_data['start_hour'],
                                        assign_data['start_hour'] + assign_data['length_in_hours'],
                                        assign_data['name'],
                                        assign_data['type']
                                    ))
                except:
                    pass
        
        session.commit()
        
        # חישוב סטטיסטיקות
        total_assignments = session.query(Assignment).filter_by(shavzak_id=shavzak_id).count()
        
        return jsonify({
            'message': 'שיבוץ בוצע בהצלחה',
            'warnings': logic.warnings,
            'stats': {
                'total_assignments': total_assignments,
                'emergency_assignments': len(logic.warnings)
            }
        }), 200
        
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/shavzakim/<int:shavzak_id>', methods=['GET'])
@token_required
def get_shavzak(shavzak_id, current_user):
    """קבלת שיבוץ"""
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
    """רשימת שיבוצים"""
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


@app.route('/api/shavzakim/<int:shavzak_id>', methods=['PUT'])
@token_required
def update_shavzak(shavzak_id, current_user):
    """עדכון שיבוץ"""
    try:
        session = get_db()

        shavzak = session.query(Shavzak).filter_by(id=shavzak_id).first()
        if not shavzak:
            return jsonify({'error': 'שיבוץ לא נמצא'}), 404

        if not can_view_shavzak(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json

        if 'name' in data:
            shavzak.name = data['name']
        if 'start_date' in data:
            shavzak.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'days_count' in data:
            shavzak.days_count = data['days_count']
        if 'min_rest_hours' in data:
            shavzak.min_rest_hours = data['min_rest_hours']
        if 'emergency_mode' in data:
            shavzak.emergency_mode = data['emergency_mode']

        session.commit()

        return jsonify({
            'message': 'שיבוץ עודכן בהצלחה',
            'shavzak': {
                'id': shavzak.id,
                'name': shavzak.name,
                'start_date': shavzak.start_date.isoformat(),
                'days_count': shavzak.days_count
            }
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/shavzakim/<int:shavzak_id>', methods=['DELETE'])
@token_required
def delete_shavzak(shavzak_id, current_user):
    """מחיקת שיבוץ"""
    try:
        session = get_db()

        shavzak = session.query(Shavzak).filter_by(id=shavzak_id).first()
        if not shavzak:
            return jsonify({'error': 'שיבוץ לא נמצא'}), 404

        if not can_view_shavzak(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        # מחיקה תמחוק גם את כל המשימות בשיבוץ בגלל cascade
        session.delete(shavzak)
        session.commit()

        return jsonify({'message': 'שיבוץ נמחק בהצלחה'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
@token_required
def update_assignment(assignment_id, current_user):
    """עדכון משימה"""
    try:
        session = get_db()

        assignment = session.query(Assignment).filter_by(id=assignment_id).first()
        if not assignment:
            return jsonify({'error': 'משימה לא נמצאה'}), 404

        shavzak = session.query(Shavzak).filter_by(id=assignment.shavzak_id).first()
        if not can_view_shavzak(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json

        if 'name' in data:
            assignment.name = data['name']
        if 'assignment_type' in data:
            assignment.assignment_type = data['assignment_type']
        if 'day' in data:
            assignment.day = data['day']
        if 'start_hour' in data:
            assignment.start_hour = data['start_hour']
        if 'length_in_hours' in data:
            assignment.length_in_hours = data['length_in_hours']
        if 'assigned_mahlaka_id' in data:
            assignment.assigned_mahlaka_id = data['assigned_mahlaka_id']

        session.commit()

        return jsonify({
            'message': 'משימה עודכנה בהצלחה',
            'assignment': {
                'id': assignment.id,
                'name': assignment.name,
                'type': assignment.assignment_type
            }
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
@token_required
def delete_assignment(assignment_id, current_user):
    """מחיקת משימה"""
    try:
        session = get_db()

        assignment = session.query(Assignment).filter_by(id=assignment_id).first()
        if not assignment:
            return jsonify({'error': 'משימה לא נמצאה'}), 404

        shavzak = session.query(Shavzak).filter_by(id=assignment.shavzak_id).first()
        if not can_view_shavzak(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        # מחיקה תמחוק גם את החיילים המשובצים בגלל cascade
        session.delete(assignment)
        session.commit()

        return jsonify({'message': 'משימה נמחקה בהצלחה'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/assignments/<int:assignment_id>/duplicate', methods=['POST'])
@token_required
def duplicate_assignment(assignment_id, current_user):
    """שכפול משימה"""
    try:
        session = get_db()

        # מציאת המשימה המקורית
        original_assignment = session.query(Assignment).filter_by(id=assignment_id).first()
        if not original_assignment:
            return jsonify({'error': 'משימה לא נמצאה'}), 404

        shavzak = session.query(Shavzak).filter_by(id=original_assignment.shavzak_id).first()
        if not can_view_shavzak(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json or {}

        # יצירת משימה חדשה עם הנתונים של המשימה המקורית
        new_assignment = Assignment(
            shavzak_id=original_assignment.shavzak_id,
            name=data.get('name', f"{original_assignment.name} (עותק)"),
            assignment_type=original_assignment.assignment_type,
            day=data.get('day', original_assignment.day),
            start_hour=data.get('start_hour', original_assignment.start_hour),
            length_in_hours=original_assignment.length_in_hours,
            assigned_mahlaka_id=original_assignment.assigned_mahlaka_id
        )

        session.add(new_assignment)
        session.flush()  # כדי לקבל את ה-ID של המשימה החדשה

        # שכפול החיילים המשובצים
        if data.get('duplicate_soldiers', False):
            original_soldiers = session.query(AssignmentSoldier).filter_by(
                assignment_id=assignment_id
            ).all()

            for soldier_assignment in original_soldiers:
                new_soldier_assignment = AssignmentSoldier(
                    assignment_id=new_assignment.id,
                    soldier_id=soldier_assignment.soldier_id,
                    role_in_assignment=soldier_assignment.role_in_assignment
                )
                session.add(new_soldier_assignment)

        session.commit()

        # החזרת המשימה החדשה עם כל הפרטים
        soldiers = []
        if data.get('duplicate_soldiers', False):
            soldier_assignments = session.query(AssignmentSoldier).filter_by(
                assignment_id=new_assignment.id
            ).all()
            for sa in soldier_assignments:
                soldier = session.query(Soldier).filter_by(id=sa.soldier_id).first()
                if soldier:
                    soldiers.append({
                        'id': soldier.id,
                        'name': soldier.name,
                        'role': sa.role_in_assignment
                    })

        return jsonify({
            'message': 'משימה שוכפלה בהצלחה',
            'assignment': {
                'id': new_assignment.id,
                'name': new_assignment.name,
                'assignment_type': new_assignment.assignment_type,
                'day': new_assignment.day,
                'start_hour': new_assignment.start_hour,
                'length_in_hours': new_assignment.length_in_hours,
                'assigned_mahlaka_id': new_assignment.assigned_mahlaka_id,
                'soldiers': soldiers
            }
        }), 201
    except Exception as e:
        session.rollback()
        print(f"Error duplicating assignment: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# JOIN REQUESTS
# ============================================================================

@app.route('/api/join-requests', methods=['GET'])
@token_required
def get_join_requests(current_user):
    """קבלת כל בקשות ההצטרפות (רק למפ ראשי)"""
    try:
        session = get_db()

        # רק מפ ראשי יכול לראות בקשות
        if current_user.role != 'מפ' or current_user.pluga_id is not None:
            return jsonify({'error': 'אין הרשאה'}), 403

        requests = session.query(JoinRequest).filter_by(status='pending').order_by(
            JoinRequest.created_at.desc()
        ).all()

        result = [{
            'id': req.id,
            'full_name': req.full_name,
            'username': req.username,
            'pluga_name': req.pluga_name,
            'gdud': req.gdud,
            'status': req.status,
            'created_at': req.created_at.isoformat()
        } for req in requests]

        return jsonify({'requests': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/join-requests/<int:request_id>/approve', methods=['POST'])
@token_required
def approve_join_request(current_user, request_id):
    """אישור בקשת הצטרפות"""
    try:
        session = get_db()

        # רק מפ ראשי יכול לאשר בקשות
        if current_user.role != 'מפ' or current_user.pluga_id is not None:
            return jsonify({'error': 'אין הרשאה'}), 403

        join_request = session.query(JoinRequest).filter_by(id=request_id).first()
        if not join_request:
            return jsonify({'error': 'בקשה לא נמצאה'}), 404

        if join_request.status != 'pending':
            return jsonify({'error': 'הבקשה כבר עובדה'}), 400

        # יצירת פלוגה חדשה עבור המפ החדש
        pluga = Pluga(
            name=join_request.pluga_name,
            gdud=join_request.gdud
        )
        session.add(pluga)
        session.flush()

        # יצירת משתמש חדש
        user = User(
            username=join_request.username,
            full_name=join_request.full_name,
            password_hash=join_request.password_hash,
            role='מפ',
            pluga_id=pluga.id
        )
        session.add(user)

        # עדכון הבקשה
        join_request.status = 'approved'
        join_request.processed_at = datetime.utcnow()
        join_request.processed_by = current_user.id

        session.commit()

        return jsonify({
            'message': 'הבקשה אושרה בהצלחה',
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'pluga_id': user.pluga_id
            },
            'pluga': {
                'id': pluga.id,
                'name': pluga.name,
                'gdud': pluga.gdud
            }
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/join-requests/<int:request_id>/reject', methods=['POST'])
@token_required
def reject_join_request(current_user, request_id):
    """דחיית בקשת הצטרפות"""
    try:
        session = get_db()

        # רק מפ ראשי יכול לדחות בקשות
        if current_user.role != 'מפ' or current_user.pluga_id is not None:
            return jsonify({'error': 'אין הרשאה'}), 403

        join_request = session.query(JoinRequest).filter_by(id=request_id).first()
        if not join_request:
            return jsonify({'error': 'בקשה לא נמצאה'}), 404

        if join_request.status != 'pending':
            return jsonify({'error': 'הבקשה כבר עובדה'}), 400

        join_request.status = 'rejected'
        join_request.processed_at = datetime.utcnow()
        join_request.processed_by = current_user.id

        session.commit()

        return jsonify({'message': 'הבקשה נדחתה'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/join-requests/<int:request_id>', methods=['DELETE'])
@token_required
def delete_join_request(current_user, request_id):
    """מחיקת בקשת הצטרפות"""
    try:
        session = get_db()

        # רק מפ ראשי יכול למחוק בקשות
        if current_user.role != 'מפ' or current_user.pluga_id is not None:
            return jsonify({'error': 'אין הרשאה'}), 403

        join_request = session.query(JoinRequest).filter_by(id=request_id).first()
        if not join_request:
            return jsonify({'error': 'בקשה לא נמצאה'}), 404

        session.delete(join_request)
        session.commit()

        return jsonify({'message': 'הבקשה נמחקה'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# LIVE/CONTINUOUS SCHEDULING
# ============================================================================

@app.route('/api/plugot/<int:pluga_id>/live-schedule', methods=['GET'])
@token_required
def get_live_schedule(pluga_id, current_user):
    """
    קבלת שיבוץ "חי" לתאריך מסוים
    המערכת מבטיחה שיבוץ לפחות 7 ימים קדימה
    """
    session = get_session()

    try:
        # בדיקת הרשאות
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה לצפות בפלוגה זו'}), 403

        # קבלת התאריך המבוקש (ברירת מחדל: מחר)
        requested_date_str = request.args.get('date')
        if requested_date_str:
            requested_date = datetime.strptime(requested_date_str, '%Y-%m-%d').date()
        else:
            requested_date = (datetime.now() + timedelta(days=1)).date()

        today = datetime.now().date()
        days_ahead = 7  # מספר ימים קדימה לבנות

        # חפש או צור Shavzak "מאסטר" לפלוגה
        master_shavzak = session.query(Shavzak).filter(
            Shavzak.pluga_id == pluga_id,
            Shavzak.name == 'שיבוץ אוטומטי'
        ).first()

        if not master_shavzak:
            # צור Shavzak מאסטר
            master_shavzak = Shavzak(
                name='שיבוץ אוטומטי',
                pluga_id=pluga_id,
                created_by_user_id=current_user['id'],
                start_date=today,
                days_count=days_ahead,
                min_rest_hours=8,
                emergency_mode=False,
                created_at=datetime.now()
            )
            session.add(master_shavzak)
            session.commit()

        # בדוק אם יש משימות לתאריך המבוקש
        # חשב את day_index יחסית ל-start_date של השיבוץ
        day_diff = (requested_date - master_shavzak.start_date).days

        # אם התאריך מחוץ לטווח הנוכחי, הרחב את השיבוץ
        max_day_needed = max((today - master_shavzak.start_date).days + days_ahead, day_diff + 1)

        if max_day_needed > master_shavzak.days_count:
            master_shavzak.days_count = max_day_needed
            session.commit()

        # בדוק אם יש משימות קיימות ליום המבוקש
        existing_assignments = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day == day_diff
        ).all()

        # אם אין משימות, צור אותן
        if not existing_assignments:
            # טען תבניות
            templates = session.query(AssignmentTemplate).filter(
                AssignmentTemplate.pluga_id == pluga_id
            ).all()

            if templates:
                # טען חיילים
                mahalkot = session.query(Mahlaka).filter(
                    Mahlaka.pluga_id == pluga_id
                ).all()

                all_soldiers = []
                for mahlaka in mahalkot:
                    soldiers = session.query(Soldier).filter(
                        Soldier.mahlaka_id == mahlaka.id
                    ).all()
                    all_soldiers.extend(soldiers)

                # חלק לקטגוריות
                commanders = []
                drivers = []
                regular_soldiers = []

                for soldier in all_soldiers:
                    soldier_data = {
                        'id': soldier.id,
                        'name': soldier.name,
                        'role': soldier.role,
                        'mahlaka_id': soldier.mahlaka_id,
                        'has_hatashab': soldier.has_hatashab or False,
                        'certifications': []
                    }

                    # טען אי-זמינויות
                    unavailable_dates = session.query(UnavailableDate).filter(
                        UnavailableDate.soldier_id == soldier.id
                    ).all()

                    soldier_data['unavailable'] = []
                    for ud in unavailable_dates:
                        # בדוק אם החייל לא זמין בתאריך המבוקש
                        if ud.end_date:
                            if ud.date <= requested_date <= ud.end_date:
                                soldier_data['unavailable'].append(requested_date.isoformat())
                        else:
                            if ud.date == requested_date:
                                soldier_data['unavailable'].append(requested_date.isoformat())

                    # סווג לפי תפקיד
                    if soldier.role in ['ממ', 'מכ', 'סמל']:
                        commanders.append(soldier_data)
                    elif soldier.role == 'נהג':
                        drivers.append(soldier_data)
                    else:
                        regular_soldiers.append(soldier_data)

                # טען אילוצים
                constraints = session.query(SchedulingConstraint).filter(
                    SchedulingConstraint.pluga_id == pluga_id,
                    SchedulingConstraint.is_active == True
                ).all()

                # המרת אילוצים למבנה נוח
                constraints_dict = []
                for c in constraints:
                    c_dict = {
                        'mahlaka_id': c.mahlaka_id,
                        'constraint_type': c.constraint_type,
                        'assignment_type': c.assignment_type,
                        'constraint_value': c.constraint_value,
                        'days_of_week': c.days_of_week,
                        'start_date': c.start_date,
                        'end_date': c.end_date
                    }
                    constraints_dict.append(c_dict)

                # יצירת logic instance
                logic = AssignmentLogic(8, False)  # 8 שעות מנוחה, לא מצב חירום

                # צור משימות לפי תבניות
                for template in templates:
                    # בדוק אם התבנית מתאימה ליום זה
                    if template.days and day_diff not in template.days:
                        continue

                    # בדוק אילוצים לפני יצירת משימה
                    skip_assignment = False
                    for constraint in constraints_dict:
                        # בדוק אם האילוץ רלוונטי
                        if constraint['mahlaka_id'] and constraint['mahlaka_id'] != template.assigned_mahlaka_id:
                            continue
                        if constraint['assignment_type'] and constraint['assignment_type'] != template.type:
                            continue

                        # אילוץ תאריכים
                        if constraint['start_date'] or constraint['end_date']:
                            if constraint['start_date'] and requested_date < constraint['start_date']:
                                continue
                            if constraint['end_date'] and requested_date > constraint['end_date']:
                                continue

                        # אם האילוץ הוא "לא יכול להשתבץ"
                        if constraint['constraint_type'] == 'cannot_assign':
                            skip_assignment = True
                            break

                    if skip_assignment:
                        continue  # דלג על המשימה הזו

                    # קרא למתודה המתאימה ב-logic
                    result = None
                    if template.type == 'סיור':
                        result = logic.assign_patrol(
                            day_diff,
                            template.start_hour,
                            template.length_in_hours,
                            commanders,
                            drivers,
                            regular_soldiers,
                            template.assigned_mahlaka_id
                        )
                    elif template.type == 'שמירה':
                        result = logic.assign_guard(
                            day_diff,
                            template.start_hour,
                            template.length_in_hours,
                            regular_soldiers
                        )
                    # ... אפשר להוסיף עוד סוגי משימות

                    if result and 'error' not in result:
                        # צור Assignment
                        assignment = Assignment(
                            shavzak_id=master_shavzak.id,
                            name=template.name,
                            type=template.type,
                            day=day_diff,
                            start_hour=template.start_hour,
                            length_in_hours=template.length_in_hours,
                            assigned_mahlaka_id=template.assigned_mahlaka_id
                        )
                        session.add(assignment)
                        session.flush()

                        # הוסף חיילים למשימה
                        for role_key in ['commanders', 'drivers', 'soldiers']:
                            if role_key in result:
                                role_name = role_key[:-1]
                                for soldier_id in result[role_key]:
                                    assign_soldier = AssignmentSoldier(
                                        assignment_id=assignment.id,
                                        soldier_id=soldier_id,
                                        role_in_assignment=role_name
                                    )
                                    session.add(assign_soldier)

                session.commit()

                # טען מחדש את המשימות
                existing_assignments = session.query(Assignment).filter(
                    Assignment.shavzak_id == master_shavzak.id,
                    Assignment.day == day_diff
                ).all()

        # בנה תגובה
        assignments_data = []
        for assignment in existing_assignments:
            # טען חיילים
            soldiers_in_assignment = session.query(AssignmentSoldier).filter(
                AssignmentSoldier.assignment_id == assignment.id
            ).all()

            soldiers_list = []
            for as_soldier in soldiers_in_assignment:
                soldier = session.query(Soldier).get(as_soldier.soldier_id)
                if soldier:
                    soldiers_list.append({
                        'id': soldier.id,
                        'name': soldier.name,
                        'role': soldier.role,
                        'role_in_assignment': as_soldier.role_in_assignment
                    })

            assignments_data.append({
                'id': assignment.id,
                'name': assignment.name,
                'type': assignment.type,
                'day': assignment.day,
                'start_hour': assignment.start_hour,
                'length_in_hours': assignment.length_in_hours,
                'assigned_mahlaka_id': assignment.assigned_mahlaka_id,
                'soldiers': soldiers_list
            })

        return jsonify({
            'date': requested_date.isoformat(),
            'date_display': requested_date.strftime('%d/%m/%Y'),
            'day_index': day_diff,
            'assignments': assignments_data,
            'shavzak_id': master_shavzak.id
        }), 200

    except Exception as e:
        session.rollback()
        print(f"Error in live schedule: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'שגיאה בטעינת שיבוץ: {str(e)}'}), 500
    finally:
        session.close()


# ============================================================================
# SCHEDULING CONSTRAINTS
# ============================================================================

def _delete_affected_assignments_by_constraint(session, pluga_id, constraint):
    """מחק משימות שמושפעות מאילוץ מסוים"""
    try:
        # מצא את השיבוץ האוטומטי
        master_shavzak = session.query(Shavzak).filter(
            Shavzak.pluga_id == pluga_id,
            Shavzak.name == 'שיבוץ אוטומטי'
        ).first()

        if not master_shavzak:
            return

        # בנה query בסיסי
        query = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id
        )

        # אם האילוץ ספציפי למחלקה, סנן לפי מחלקה
        if constraint.mahlaka_id:
            query = query.filter(Assignment.assigned_mahlaka_id == constraint.mahlaka_id)

        # אם האילוץ ספציפי לסוג משימה, סנן לפי סוג
        if constraint.assignment_type:
            query = query.filter(Assignment.type == constraint.assignment_type)

        # אם יש טווח תאריכים, סנן לפי תאריכים
        if constraint.start_date or constraint.end_date:
            shavzak_start = master_shavzak.start_date
            if constraint.start_date:
                start_day = (constraint.start_date - shavzak_start).days
                query = query.filter(Assignment.day >= start_day)
            if constraint.end_date:
                end_day = (constraint.end_date - shavzak_start).days
                query = query.filter(Assignment.day <= end_day)

        # מחק את המשימות המושפעות
        affected_assignments = query.all()
        for assignment in affected_assignments:
            # מחק את כל השיוכים של המשימה
            session.query(AssignmentSoldier).filter(
                AssignmentSoldier.assignment_id == assignment.id
            ).delete()
            # מחק את המשימה עצמה
            session.delete(assignment)

    except Exception as e:
        print(f"Error deleting affected assignments: {str(e)}")
        # לא נעצור את התהליך - רק נדווח


@app.route('/api/plugot/<int:pluga_id>/constraints', methods=['GET'])
@token_required
def get_constraints(pluga_id, current_user):
    """קבלת כל האילוצים של פלוגה"""
    session = get_session()
    try:
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        constraints = session.query(SchedulingConstraint).filter(
            SchedulingConstraint.pluga_id == pluga_id,
            SchedulingConstraint.is_active == True
        ).all()

        constraints_data = []
        for c in constraints:
            mahlaka_name = None
            if c.mahlaka_id:
                mahlaka = session.query(Mahlaka).get(c.mahlaka_id)
                if mahlaka:
                    mahlaka_name = f"מחלקה {mahlaka.number}"

            constraints_data.append({
                'id': c.id,
                'mahlaka_id': c.mahlaka_id,
                'mahlaka_name': mahlaka_name,
                'constraint_type': c.constraint_type,
                'assignment_type': c.assignment_type,
                'constraint_value': c.constraint_value,
                'days_of_week': c.days_of_week,
                'start_date': c.start_date.isoformat() if c.start_date else None,
                'end_date': c.end_date.isoformat() if c.end_date else None,
                'reason': c.reason,
                'created_at': c.created_at.isoformat()
            })

        return jsonify({'constraints': constraints_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/plugot/<int:pluga_id>/constraints', methods=['POST'])
@token_required
@role_required(['מפ', 'ממ'])
def create_constraint(pluga_id, current_user):
    """יצירת אילוץ חדש"""
    session = get_session()
    try:
        if not can_edit_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json

        # המרת תאריכים
        start_date = None
        end_date = None
        if data.get('start_date'):
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if data.get('end_date'):
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

        constraint = SchedulingConstraint(
            pluga_id=pluga_id,
            mahlaka_id=data.get('mahlaka_id'),
            constraint_type=data['constraint_type'],
            assignment_type=data.get('assignment_type'),
            constraint_value=data.get('constraint_value'),
            days_of_week=data.get('days_of_week'),
            start_date=start_date,
            end_date=end_date,
            reason=data.get('reason'),
            is_active=True,
            created_by=current_user['id']
        )

        session.add(constraint)
        session.flush()

        # מחק שיבוצים מושפעים מהאילוץ החדש
        _delete_affected_assignments_by_constraint(session, pluga_id, constraint)

        session.commit()

        return jsonify({
            'message': 'אילוץ נוצר בהצלחה',
            'constraint': {
                'id': constraint.id,
                'constraint_type': constraint.constraint_type
            }
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/constraints/<int:constraint_id>', methods=['DELETE'])
@token_required
@role_required(['מפ', 'ממ'])
def delete_constraint(constraint_id, current_user):
    """מחיקת אילוץ"""
    session = get_session()
    try:
        constraint = session.query(SchedulingConstraint).get(constraint_id)
        if not constraint:
            return jsonify({'error': 'אילוץ לא נמצא'}), 404

        if not can_edit_pluga(current_user, constraint.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        pluga_id = constraint.pluga_id

        # במקום למחוק, נסמן כלא פעיל
        constraint.is_active = False
        session.flush()

        # מחק שיבוצים שהיו מושפעים מהאילוץ הזה
        # (כדי שיבנו מחדש בלי האילוץ)
        _delete_affected_assignments_by_constraint(session, pluga_id, constraint)

        session.commit()

        return jsonify({'message': 'אילוץ נמחק בהצלחה'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# SOLDIER STATUS
# ============================================================================

@app.route('/api/soldiers/<int:soldier_id>/status', methods=['GET'])
@token_required
def get_soldier_status(soldier_id, current_user):
    """קבלת סטטוס נוכחי של חייל"""
    session = get_session()
    try:
        soldier = session.query(Soldier).get(soldier_id)
        if not soldier:
            return jsonify({'error': 'חייל לא נמצא'}), 404

        # בדוק אם החייל בסבב קו
        in_round = False
        if soldier.home_round_date:
            today = datetime.now().date()
            days_diff = (today - soldier.home_round_date).days
            cycle_position = days_diff % 21
            in_round = cycle_position < 4  # ימים 0-3 = בסבב

        # קבל את הסטטוס הנוכחי או צור חדש
        status = session.query(SoldierStatus).filter_by(soldier_id=soldier_id).first()
        if not status:
            status = SoldierStatus(soldier_id=soldier_id, status_type='בבסיס')
            session.add(status)
            session.commit()

        return jsonify({
            'status': {
                'id': status.id,
                'status_type': status.status_type,
                'return_date': status.return_date.isoformat() if status.return_date else None,
                'notes': status.notes,
                'updated_at': status.updated_at.isoformat() if status.updated_at else None
            },
            'in_round': in_round
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/soldiers/<int:soldier_id>/status', methods=['PUT'])
@token_required
def update_soldier_status(soldier_id, current_user):
    """עדכון סטטוס של חייל"""
    session = get_session()
    try:
        if not can_edit_soldier(current_user, soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json
        status_type = data.get('status_type', 'בבסיס')
        return_date = data.get('return_date')
        notes = data.get('notes', '')

        # המרת תאריך
        return_date_obj = None
        if return_date:
            return_date_obj = datetime.strptime(return_date, '%Y-%m-%d').date()

        # קבל או צור סטטוס
        status = session.query(SoldierStatus).filter_by(soldier_id=soldier_id).first()
        if not status:
            status = SoldierStatus(soldier_id=soldier_id)
            session.add(status)

        status.status_type = status_type
        status.return_date = return_date_obj
        status.notes = notes
        status.updated_by = current_user['id']
        status.updated_at = datetime.now()

        session.flush()

        # מחק שיבוצים מושפעים אם החייל לא בבסיס
        if status_type != 'בבסיס':
            soldier = session.query(Soldier).get(soldier_id)
            if soldier and soldier.mahlaka_id:
                mahlaka = session.query(Mahlaka).get(soldier.mahlaka_id)
                if mahlaka and mahlaka.pluga_id:
                    master_shavzak = session.query(Shavzak).filter(
                        Shavzak.pluga_id == mahlaka.pluga_id,
                        Shavzak.name == 'שיבוץ אוטומטי'
                    ).first()

                    if master_shavzak:
                        today = datetime.now().date()
                        shavzak_start = master_shavzak.start_date
                        start_day = (today - shavzak_start).days
                        end_day = start_day + 30  # מחק 30 ימים קדימה

                        if return_date_obj:
                            end_day = min(end_day, (return_date_obj - shavzak_start).days)

                        for day in range(max(0, start_day), end_day + 1):
                            soldier_assignments = session.query(AssignmentSoldier).join(Assignment).filter(
                                AssignmentSoldier.soldier_id == soldier_id,
                                Assignment.shavzak_id == master_shavzak.id,
                                Assignment.day == day
                            ).all()

                            for sa in soldier_assignments:
                                assignment = session.query(Assignment).get(sa.assignment_id)
                                if assignment:
                                    session.query(AssignmentSoldier).filter(
                                        AssignmentSoldier.assignment_id == assignment.id
                                    ).delete()
                                    session.delete(assignment)

        session.commit()

        return jsonify({
            'message': 'סטטוס עודכן בהצלחה',
            'status': {
                'status_type': status.status_type,
                'return_date': status.return_date.isoformat() if status.return_date else None
            }
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# UTILITY
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """בדיקת תקינות"""
    return jsonify({
        'status': 'healthy',
        'message': 'Shavzak API is running'
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'נתיב לא נמצא'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'שגיאת שרת פנימית'}), 500


if __name__ == '__main__':
    print("🎖️  Shavzak API Server Starting...")
    print("=" * 70)
    print("📋 Database initialized")
    print("🔐 Authentication enabled")
    print("🚀 Server running on http://localhost:5000")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
