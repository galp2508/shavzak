"""
Shavzak API Server
מערכת ניהול שיבוצים צבאית
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from sqlalchemy import func
import traceback
import re

from models import (
    init_db, get_session, User, Pluga, Mahlaka, Soldier,
    Certification, UnavailableDate, AssignmentTemplate,
    Shavzak, Assignment, AssignmentSoldier, JoinRequest,
    SchedulingConstraint, SoldierStatus
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

        # בדיקה 3: הוספת hatash_2_days לטבלת soldiers
        cursor.execute("PRAGMA table_info(soldiers)")
        soldier_columns = [column[1] for column in cursor.fetchall()]

        if 'hatash_2_days' not in soldier_columns:
            print("⚠️  מזהה עמודה חסרה: hatash_2_days")
            print("🔧 מריץ migration אוטומטי להוספת hatash_2_days...")
            conn.close()
            from migrate_add_hatash_2_days import migrate_database as migrate_add_hatash_2
            if migrate_add_hatash_2(DB_PATH):
                print("✅ Migration להוספת hatash_2_days הושלם בהצלחה")
            else:
                print("❌ Migration להוספת hatash_2_days נכשל")
                return False
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
        else:
            print("✅ hatash_2_days כבר קיים")

        # בדיקה 4: הוספת start_hour לטבלת assignment_templates
        cursor.execute("PRAGMA table_info(assignment_templates)")
        template_columns = [column[1] for column in cursor.fetchall()]

        if 'start_hour' not in template_columns:
            print("⚠️  מזהה עמודה חסרה: start_hour")
            print("🔧 מריץ migration אוטומטי להוספת start_hour...")
            conn.close()
            from migrate_add_start_hour import migrate_database as migrate_add_start_hour
            if migrate_add_start_hour(DB_PATH):
                print("✅ Migration להוספת start_hour הושלם בהצלחה")
            else:
                print("❌ Migration להוספת start_hour נכשל")
                return False
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
        else:
            print("✅ start_hour כבר קיים")

        # בדיקה 5: הוספת reuse_soldiers_for_standby לטבלת shavzakim
        cursor.execute("PRAGMA table_info(shavzakim)")
        shavzak_columns = [column[1] for column in cursor.fetchall()]

        if 'reuse_soldiers_for_standby' not in shavzak_columns:
            print("⚠️  מזהה עמודה חסרה: reuse_soldiers_for_standby בטבלת shavzakim")
            print("🔧 מריץ migration אוטומטי להוספת reuse_soldiers_for_standby...")
            conn.close()
            from migrate_add_reuse_soldiers import migrate
            try:
                migrate()
                print("✅ Migration להוספת reuse_soldiers_for_standby לשיבוצים הושלם בהצלחה")
            except Exception as e:
                print(f"❌ Migration להוספת reuse_soldiers_for_standby נכשל: {e}")
                return False
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
        else:
            print("✅ reuse_soldiers_for_standby בטבלת shavzakim כבר קיים")

        # בדיקה 6: הוספת reuse_soldiers_for_standby לטבלת assignment_templates
        cursor.execute("PRAGMA table_info(assignment_templates)")
        template_columns = [column[1] for column in cursor.fetchall()]

        if 'reuse_soldiers_for_standby' not in template_columns:
            print("⚠️  מזהה עמודה חסרה: reuse_soldiers_for_standby בטבלת assignment_templates")
            print("🔧 מריץ migration אוטומטי להוספת reuse_soldiers_for_standby לתבניות...")
            conn.close()
            from migrate_add_reuse_to_templates import migrate as migrate_templates
            try:
                migrate_templates()
                print("✅ Migration להוספת reuse_soldiers_for_standby לתבניות הושלם בהצלחה")
            except Exception as e:
                print(f"❌ Migration להוספת reuse_soldiers_for_standby לתבניות נכשל: {e}")
                return False
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
        else:
            print("✅ reuse_soldiers_for_standby בטבלת assignment_templates כבר קיים")

        conn.close()
        return True
    except Exception as e:
        print(f"⚠️  שגיאה בבדיקת schema: {e}")
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return False

# הרצת migrations בעת אתחול
check_and_run_migrations()

# Error handlers להצגת שגיאות מפורטות בקונסול
@app.errorhandler(Exception)
def handle_exception(e):
    """טיפול גלובלי בשגיאות - הצגת traceback מלא בקונסול"""
    print("=" * 80)
    print("🔴 שגיאה לא צפויה:")
    print("=" * 80)
    traceback.print_exc()
    print("=" * 80)

    # החזר תשובה ידידותית ללקוח
    return jsonify({
        'error': 'שגיאת שרת פנימית',
        'message': str(e),
        'type': type(e).__name__
    }), 500

@app.errorhandler(404)
def not_found(e):
    """טיפול ב-404"""
    print(f"⚠️  404 Not Found: {request.url}")
    return jsonify({'error': 'הנתיב לא נמצא'}), 404

@app.errorhandler(400)
def bad_request(e):
    """טיפול ב-400"""
    print(f"⚠️  400 Bad Request: {str(e)}")
    traceback.print_exc()
    return jsonify({'error': 'בקשה לא תקינה', 'message': str(e)}), 400

def get_db():
    """מקבל session של DB"""
    return get_session(engine)


def build_user_response(user):
    """Build user response with full pluga and mahlaka objects"""
    user_data = {
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'role': user.role,
        'pluga_id': user.pluga_id,
        'mahlaka_id': user.mahlaka_id,
        'kita': user.kita
    }

    # Add full pluga object if user has a pluga
    if user.pluga:
        user_data['pluga'] = {
            'id': user.pluga.id,
            'name': user.pluga.name,
            'color': user.pluga.color,
            'gdud': user.pluga.gdud
        }

    # Add full mahlaka object if user has a mahlaka
    if user.mahlaka:
        user_data['mahlaka'] = {
            'id': user.mahlaka.id,
            'number': user.mahlaka.number,
            'color': user.mahlaka.color
        }

    return user_data


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
                'user': build_user_response(user)
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
                    'user': build_user_response(user)
                }), 201

    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
            'user': build_user_response(user)
        }), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """קבלת פרטי המשתמש הנוכחי"""
    try:
        session = get_db()
        user = session.query(User).filter_by(id=current_user.get('user_id')).first()

        if not user:
            return jsonify({'error': 'משתמש לא נמצא'}), 404

        return jsonify({
            'user': build_user_response(user)
        }), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        
        if current_user.get('role') == 'ממ':
            if data['role'] != 'מכ' or data.get('mahlaka_id') != current_user.get('mahlaka_id'):
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
            'user': build_user_response(user)
        }), 201
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        
        user = session.query(User).filter_by(id=current_user.get('user_id')).first()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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

        pluga_id = data.get('pluga_id', current_user.get('pluga_id'))

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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/mahalkot/<int:mahlaka_id>', methods=['PUT'])
@token_required
def update_mahlaka(mahlaka_id, current_user):
    """עדכון פרטי מחלקה (צבע, מספר)"""
    try:
        session = get_db()

        if not can_edit_mahlaka(current_user, mahlaka_id, session):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        mahlaka = session.query(Mahlaka).filter_by(id=mahlaka_id).first()
        if not mahlaka:
            return jsonify({'error': 'מחלקה לא נמצאה'}), 404

        data = request.json

        # עדכון צבע
        if 'color' in data:
            mahlaka.color = data['color']

        # עדכון מספר מחלקה
        if 'number' in data:
            mahlaka.number = data['number']

        session.commit()

        return jsonify({
            'message': 'מחלקה עודכנה בהצלחה',
            'mahlaka': {
                'id': mahlaka.id,
                'number': mahlaka.number,
                'color': mahlaka.color
            }
        }), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        
        pluga_id = data.get('pluga_id', current_user.get('pluga_id'))

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
                error_msg = f"שורה {idx + 1}: {str(e)}"
                errors.append(error_msg)
                print(f"🔴 שגיאה בייבוא: {error_msg}")
                traceback.print_exc()
        
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        
        if current_user.get('role') == 'מכ':
            if data.get('kita') != current_user.get('kita'):
                return jsonify({'error': 'אתה יכול להוסיף חיילים רק לכיתה שלך'}), 403
        
        soldier = Soldier(
            name=data['name'],
            role=data['role'],
            mahlaka_id=mahlaka_id,
            kita=data.get('kita'),
            idf_id=data.get('idf_id') or None,
            personal_id=data.get('personal_id') or None,
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
                if current_user.get('role') == 'מכ':
                    if soldier_data.get('kita') != current_user.get('kita'):
                        errors.append(f"שורה {idx + 1}: אתה יכול להוסיף חיילים רק לכיתה שלך")
                        continue
                
                # Create soldier
                soldier = Soldier(
                    name=soldier_data['name'],
                    role=soldier_data['role'],
                    mahlaka_id=mahlaka_id,
                    kita=soldier_data.get('kita'),
                    idf_id=soldier_data.get('idf_id') or None,
                    personal_id=soldier_data.get('personal_id') or None,
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
                        if date_str:  # רק אם התאריך לא ריק
                            # תמיכה בשני פורמטים: DD.MM.YYYY או YYYY-MM-DD
                            try:
                                unavailable = datetime.strptime(date_str, '%d.%m.%Y').date()
                            except ValueError:
                                try:
                                    unavailable = datetime.strptime(date_str, '%Y-%m-%d').date()
                                except ValueError:
                                    # אם לא הצלחנו לפרסר, נוסיף הודעת שגיאה ברורה
                                    errors.append(f"שורה {idx + 1} ({soldier_data.get('name', 'לא ידוע')}): פורמט תאריך לא חוקי: {date_str}. השתמש ב-DD.MM.YYYY או YYYY-MM-DD")
                                    raise ValueError("Invalid date format")

                            unavailable_record = UnavailableDate(soldier_id=soldier.id, date=unavailable)
                            session.add(unavailable_record)

                            # עדכון סטטוס החייל ל-"בסבב קו" עם תאריך חזרה
                            soldier_status = session.query(SoldierStatus).filter_by(soldier_id=soldier.id).first()
                            if not soldier_status:
                                soldier_status = SoldierStatus(
                                    soldier_id=soldier.id,
                                    status_type='בסבב קו',
                                    return_date=unavailable
                                )
                                session.add(soldier_status)
                            else:
                                soldier_status.status_type = 'בסבב קו'
                                soldier_status.return_date = unavailable

                            print(f"✅ נשמר תאריך יציאה {unavailable} לחייל {soldier_data.get('name')} + עודכן סטטוס ל-'בסבב קו'")
                    except ValueError:
                        # שגיאת פורמט - כבר טיפלנו בזה למעלה
                        pass
                    except Exception as e:
                        # שגיאה אחרת - נדווח
                        errors.append(f"שורה {idx + 1} ({soldier_data.get('name', 'לא ידוע')}): שגיאה בשמירת תאריך יציאה: {str(e)}")
                        print(f"🔴 Error saving unavailable_date for {soldier_data.get('name')}: {str(e)}")
                        traceback.print_exc()
                
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
                error_msg = f"שורה {idx + 1}: {str(e)}"
                errors.append(error_msg)
                print(f"🔴 שגיאה בייבוא: {error_msg}")
                traceback.print_exc()
        
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
                'hatash_2_days': soldier.hatash_2_days,
                'mahlaka_id': soldier.mahlaka_id,
                'certifications': cert_list,
                'unavailable_dates': unavailable_list
            }
        }), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        if 'hatash_2_days' in data:
            soldier.hatash_2_days = data['hatash_2_days'] if data['hatash_2_days'] else None

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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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

        if current_user.get('role') == 'מכ':
            soldiers = [s for s in soldiers if s.kita == current_user.get('kita')]

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
                'hatash_2_days': soldier.hatash_2_days,
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
        import traceback
        print(f"Error in list_soldiers_by_mahlaka: {str(e)}")
        print(traceback.format_exc())
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
            start_hour=data.get('start_hour'),
            commanders_needed=data.get('commanders_needed', 0),
            drivers_needed=data.get('drivers_needed', 0),
            soldiers_needed=data.get('soldiers_needed', 0),
            same_mahlaka_required=data.get('same_mahlaka_required', False),
            requires_certification=data.get('requires_certification'),
            requires_senior_commander=data.get('requires_senior_commander', False),
            reuse_soldiers_for_standby=data.get('reuse_soldiers_for_standby', False)
        )
        
        session.add(template)
        session.commit()

        # מחק את השיבוץ האוטומטי כדי שייווצר מחדש עם התבנית החדשה
        _trigger_schedule_regeneration(session, pluga_id)
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
            'start_hour': t.start_hour,
            'commanders_needed': t.commanders_needed,
            'drivers_needed': t.drivers_needed,
            'soldiers_needed': t.soldiers_needed,
            'same_mahlaka_required': t.same_mahlaka_required,
            'requires_certification': t.requires_certification,
            'requires_senior_commander': t.requires_senior_commander,
            'reuse_soldiers_for_standby': t.reuse_soldiers_for_standby
        } for t in templates]

        return jsonify({'templates': result}), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        if 'start_hour' in data:
            template.start_hour = data['start_hour']
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
        if 'reuse_soldiers_for_standby' in data:
            template.reuse_soldiers_for_standby = data['reuse_soldiers_for_standby']

        session.commit()

        # מחק את השיבוץ האוטומטי כדי שייווצר מחדש עם התבנית המעודכנת
        _trigger_schedule_regeneration(session, template.pluga_id)
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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

        pluga_id = template.pluga_id
        session.delete(template)
        session.commit()

        # מחק את השיבוץ האוטומטי כדי שייווצר מחדש ללא התבנית שנמחקה
        _trigger_schedule_regeneration(session, pluga_id)
        session.commit()

        return jsonify({'message': 'תבנית נמחקה בהצלחה'}), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
            requires_senior_commander=original_template.requires_senior_commander,
            reuse_soldiers_for_standby=original_template.reuse_soldiers_for_standby
        )

        session.add(new_template)
        session.commit()

        # מחק את השיבוץ האוטומטי כדי שייווצר מחדש עם התבנית המשוכפלת
        _trigger_schedule_regeneration(session, original_template.pluga_id)
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
        
        pluga_id = data.get('pluga_id', current_user.get('pluga_id'))

        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        shavzak = Shavzak(
            pluga_id=pluga_id,
            name=data['name'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            days_count=data['days_count'],
            created_by=current_user.get('user_id'),
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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

                # קבל סטטוס נוכחי
                status = session.query(SoldierStatus).filter_by(soldier_id=soldier.id).first()

                soldier_data = {
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'kita': soldier.kita,
                    'certifications': cert_list,
                    'unavailable_dates': unavailable_dates,
                    'hatash_2_days': soldier.hatash_2_days,
                    'status_type': status.status_type if status else 'בבסיס',
                    'mahlaka_id': mahlaka.id  # חשוב ל-ML!
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
        
        # פונקציה לבדיקת זמינות חייל ביום מסוים
        def is_soldier_available(soldier_data, check_date):
            """בודק אם חייל זמין ביום מסוים, תוך התחשבות בהתש"ב 2 וריתוק"""
            # אם החייל בריתוק, הוא לא זמין (ריתוק מבטל הכל)
            if soldier_data.get('status_type') == 'ריתוק':
                return False

            # בדוק אם התאריך באי זמינות רגילה
            if check_date in soldier_data.get('unavailable_dates', []):
                return False

            # בדוק התש"ב 2 - ימים קבועים שהחייל לא זמין
            hatash_2_days = soldier_data.get('hatash_2_days')
            if hatash_2_days:
                day_of_week = check_date.weekday()  # 0=Monday, 6=Sunday
                # התאם ל-0=Sunday כמו שמצפים בממשק
                day_of_week = (day_of_week + 1) % 7
                hatash_days_list = hatash_2_days.split(',')
                if str(day_of_week) in hatash_days_list:
                    return False

            return True

        # אתחול אלגוריתם
        logic = AssignmentLogic(
            min_rest_hours=shavzak.min_rest_hours,
            reuse_soldiers_for_standby=shavzak.reuse_soldiers_for_standby
        )
        
        # יצירת משימות
        all_assignments = []
        for day in range(shavzak.days_count):
            current_date = shavzak.start_date + timedelta(days=day)
            
            for template in templates:
                for slot in range(template.times_per_day):
                    # אם start_hour מוגדר בתבנית, השתמש בו. אחרת, חשב אוטומטית
                    if template.start_hour is not None:
                        start_hour = template.start_hour + (slot * template.length_in_hours)
                    else:
                        start_hour = slot * template.length_in_hours

                    # שם המשימה - ללא מספר סלוט! כל המשימות של אותה תבנית יוצגו באותה עמודה
                    # אבל בשורות שונות לפי שעת ההתחלה
                    assign_data = {
                        'name': template.name,
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
                        'reuse_soldiers_for_standby': template.reuse_soldiers_for_standby,
                        'date': current_date
                    }
                    
                    all_assignments.append(assign_data)
        
        # מיון לפי יום ושעה, עם כוננויות אחרונות (כדי שחיילים שסיימו משימה יוכלו להמשיך לכוננות)
        def assignment_priority(assign):
            # כוננויות אחרונות באותה שעה
            is_standby = assign['type'] in ['כוננות א', 'כוננות ב']
            priority = 1 if is_standby else 0
            return (assign['day'], assign['start_hour'], priority)

        all_assignments.sort(key=assignment_priority)
        
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
                
                # סינון חיילים לא זמינים (כולל התש"ב 2 וריתוק)
                available_mahalkot = []
                for mahlaka_info in mahalkot_data:
                    available_commanders = [
                        c for c in mahlaka_info['commanders']
                        if is_soldier_available(c, current_date)
                    ]
                    available_drivers = [
                        d for d in mahlaka_info['drivers']
                        if is_soldier_available(d, current_date)
                    ]
                    available_soldiers = [
                        s for s in mahlaka_info['soldiers']
                        if is_soldier_available(s, current_date)
                    ]

                    available_mahalkot.append({
                        'id': mahlaka_info['id'],
                        'number': mahlaka_info['number'],
                        'commanders': available_commanders,
                        'drivers': available_drivers,
                        'soldiers': available_soldiers
                    })

                available_commanders = [c for c in all_commanders if is_soldier_available(c, current_date)]
                available_drivers = [d for d in all_drivers if is_soldier_available(d, current_date)]
                available_soldiers = [s for s in all_soldiers if is_soldier_available(s, current_date)]

                # שימוש ב-SmartScheduler (ML) - מערכת חכמה שלומדת מפידבק!
                all_available = available_commanders + available_drivers + available_soldiers
                result = smart_scheduler.assign_task(assign_data, all_available, schedules, mahlaka_workload)

                # אם ML נכשל - נסה עם AssignmentLogic הישן (גיבוי)
                if not result:
                    print(f"🔄 ML נכשל ל-{assign_data['name']}, מנסה עם AssignmentLogic...")
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
                        result = logic.assign_hafak_gashash(assign_data, available_soldiers, schedules)
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

                    # וידוא שה-assignment נוצר כראוי
                    if not assignment.id:
                        raise ValueError(f"שגיאה ביצירת משימה '{assign_data['name']}' ליום {assign_data['day']} - לא ניתן היה לשמור את המשימה במסד הנתונים")

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
                error_msg = str(e)
                failed_assignments.append((assign_data, error_msg))
                print(f"🔴 שגיאה ביצירת שיבוץ: {error_msg}")
                traceback.print_exc()
        
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
                                         if is_soldier_available(c, current_date)],
                            'drivers': [d for d in mahlaka_info['drivers']
                                       if is_soldier_available(d, current_date)],
                            'soldiers': [s for s in mahlaka_info['soldiers']
                                        if is_soldier_available(s, current_date)]
                        })

                    available_commanders = [c for c in all_commanders if is_soldier_available(c, current_date)]
                    available_drivers = [d for d in all_drivers if is_soldier_available(d, current_date)]
                    available_soldiers = [s for s in all_soldiers if is_soldier_available(s, current_date)]
                    
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

                        # וידוא שה-assignment נוצר כראוי (במצב חירום)
                        if not assignment.id:
                            continue  # דלג על משימה זו במצב חירום

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

        # עדכון וושמירת מודל ML
        smart_scheduler.stats['total_assignments'] += total_assignments
        smart_scheduler.stats['successful_assignments'] += total_assignments
        smart_scheduler.save_model(ML_MODEL_PATH)
        print(f"✅ מודל ML נשמר עם {total_assignments} משימות חדשות")

        return jsonify({
            'message': 'שיבוץ בוצע בהצלחה (ML חכם!)',
            'warnings': logic.warnings,
            'stats': {
                'total_assignments': total_assignments,
                'emergency_assignments': len(logic.warnings),
                'ml_stats': smart_scheduler.get_stats()
            }
        }), 200
        
    except Exception as e:
        session.rollback()
        traceback.print_exc()

        # הפקת הודעת שגיאה ברורה
        error_msg = str(e)
        detailed_error = 'שגיאה לא ידועה בשיבוץ'

        # זיהוי סוגי שגיאות נפוצות
        if 'NoneType' in error_msg and 'id' in error_msg:
            detailed_error = 'שגיאה ביצירת משימה - המערכת לא הצליחה לשמור משימה במסד הנתונים. ייתכן שיש בעיה בהגדרות הפלוגה או במסד הנתונים.'
        elif 'no such column' in error_msg.lower():
            detailed_error = 'שגיאת מסד נתונים - חסר שדה במסד הנתונים. יש לפנות למנהל המערכת.'
        elif 'foreign key' in error_msg.lower():
            detailed_error = 'שגיאה בקשרים - אחד הנתונים (פלוגה, מחלקה או חייל) אינו תקין במערכת.'
        elif 'לא קיימות תבניות משימות' in error_msg:
            detailed_error = 'אין תבניות משימות מוגדרות במערכת. יש להגדיר תבניות משימות לפני יצירת שיבוץ אוטומטי.'
        elif 'לא ניתן היה לשמור את המשימה' in error_msg:
            detailed_error = error_msg  # השגיאה כבר ברורה

        return jsonify({
            'error': detailed_error,
            'technical_details': error_msg
        }), 500
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
                'role': s.AssignmentSoldier.role_in_assignment,
                'mahlaka_id': s.Soldier.mahlaka_id
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
                        'role': sa.role_in_assignment,
                        'mahlaka_id': soldier.mahlaka_id
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


@app.route('/api/shavzakim/<int:shavzak_id>/assignments', methods=['POST'])
@token_required
def create_manual_assignment(shavzak_id, current_user):
    """יצירת משימה חדשה באופן ידני"""
    try:
        session = get_db()

        # בדיקת הרשאות
        shavzak = session.query(Shavzak).filter_by(id=shavzak_id).first()
        if not shavzak:
            return jsonify({'error': 'שבצ"ק לא נמצא'}), 404

        if not can_edit_pluga(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json

        # יצירת המשימה
        assignment = Assignment(
            shavzak_id=shavzak_id,
            name=data['name'],
            assignment_type=data['assignment_type'],
            day=data['day'],
            start_hour=data['start_hour'],
            length_in_hours=data['length_in_hours'],
            assigned_mahlaka_id=data.get('assigned_mahlaka_id')
        )

        session.add(assignment)
        session.flush()  # כדי לקבל את ה-ID

        # הוספת חיילים אם קיימים
        if 'soldiers' in data and data['soldiers']:
            for soldier_data in data['soldiers']:
                soldier_assignment = AssignmentSoldier(
                    assignment_id=assignment.id,
                    soldier_id=soldier_data['soldier_id'],
                    role_in_assignment=soldier_data['role']
                )
                session.add(soldier_assignment)

        session.commit()

        # בניית תגובה עם פרטי המשימה
        soldiers = []
        soldier_assignments = session.query(AssignmentSoldier).filter_by(
            assignment_id=assignment.id
        ).all()

        for sa in soldier_assignments:
            soldier = session.query(Soldier).filter_by(id=sa.soldier_id).first()
            if soldier:
                soldiers.append({
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'role_in_assignment': sa.role_in_assignment,
                    'mahlaka_id': soldier.mahlaka_id
                })

        return jsonify({
            'message': 'משימה נוצרה בהצלחה',
            'assignment': {
                'id': assignment.id,
                'name': assignment.name,
                'type': assignment.assignment_type,
                'day': assignment.day,
                'start_hour': assignment.start_hour,
                'length_in_hours': assignment.length_in_hours,
                'assigned_mahlaka_id': assignment.assigned_mahlaka_id,
                'soldiers': soldiers
            }
        }), 201
    except Exception as e:
        print(f"🔴 שגיאה ביצירת משימה ידנית: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
@token_required
def update_assignment(assignment_id, current_user):
    """עדכון משימה קיימת"""
    try:
        session = get_db()

        assignment = session.query(Assignment).filter_by(id=assignment_id).first()
        if not assignment:
            return jsonify({'error': 'משימה לא נמצאה'}), 404

        shavzak = session.query(Shavzak).filter_by(id=assignment.shavzak_id).first()
        if not can_edit_pluga(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json

        # עדכון שדות המשימה
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

        # החזרת המשימה המעודכנת
        soldiers = []
        soldier_assignments = session.query(AssignmentSoldier).filter_by(
            assignment_id=assignment.id
        ).all()

        for sa in soldier_assignments:
            soldier = session.query(Soldier).filter_by(id=sa.soldier_id).first()
            if soldier:
                soldiers.append({
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'role_in_assignment': sa.role_in_assignment,
                    'mahlaka_id': soldier.mahlaka_id
                })

        return jsonify({
            'message': 'משימה עודכנה בהצלחה',
            'assignment': {
                'id': assignment.id,
                'name': assignment.name,
                'type': assignment.assignment_type,
                'day': assignment.day,
                'start_hour': assignment.start_hour,
                'length_in_hours': assignment.length_in_hours,
                'assigned_mahlaka_id': assignment.assigned_mahlaka_id,
                'soldiers': soldiers
            }
        }), 200
    except Exception as e:
        print(f"🔴 שגיאה בעדכון משימה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/assignments/<int:assignment_id>/soldiers', methods=['PUT'])
@token_required
def update_assignment_soldiers(assignment_id, current_user):
    """עדכון החיילים המשובצים למשימה"""
    try:
        session = get_db()

        assignment = session.query(Assignment).filter_by(id=assignment_id).first()
        if not assignment:
            return jsonify({'error': 'משימה לא נמצאה'}), 404

        shavzak = session.query(Shavzak).filter_by(id=assignment.shavzak_id).first()
        if not can_edit_pluga(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json

        # מחיקת כל החיילים הקיימים
        session.query(AssignmentSoldier).filter_by(assignment_id=assignment_id).delete()

        # הוספת החיילים החדשים
        if 'soldiers' in data and data['soldiers']:
            for soldier_data in data['soldiers']:
                soldier_assignment = AssignmentSoldier(
                    assignment_id=assignment_id,
                    soldier_id=soldier_data['soldier_id'],
                    role_in_assignment=soldier_data['role']
                )
                session.add(soldier_assignment)

        session.commit()

        # החזרת רשימת החיילים המעודכנת
        soldiers = []
        soldier_assignments = session.query(AssignmentSoldier).filter_by(
            assignment_id=assignment_id
        ).all()

        for sa in soldier_assignments:
            soldier = session.query(Soldier).filter_by(id=sa.soldier_id).first()
            if soldier:
                soldiers.append({
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'role_in_assignment': sa.role_in_assignment,
                    'mahlaka_id': soldier.mahlaka_id
                })

        return jsonify({
            'message': 'חיילים עודכנו בהצלחה',
            'soldiers': soldiers
        }), 200
    except Exception as e:
        print(f"🔴 שגיאה בעדכון חיילים: {str(e)}")
        traceback.print_exc()
        session.rollback()
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
        if current_user.get('role') != 'מפ' or current_user.get('pluga_id') is not None:
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        if current_user.get('role') != 'מפ' or current_user.get('pluga_id') is not None:
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
        join_request.processed_by = current_user.get('user_id')

        session.commit()

        return jsonify({
            'message': 'הבקשה אושרה בהצלחה',
            'user': build_user_response(user),
            'pluga': {
                'id': pluga.id,
                'name': pluga.name,
                'gdud': pluga.gdud
            }
        }), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        if current_user.get('role') != 'מפ' or current_user.get('pluga_id') is not None:
            return jsonify({'error': 'אין הרשאה'}), 403

        join_request = session.query(JoinRequest).filter_by(id=request_id).first()
        if not join_request:
            return jsonify({'error': 'בקשה לא נמצאה'}), 404

        if join_request.status != 'pending':
            return jsonify({'error': 'הבקשה כבר עובדה'}), 400

        join_request.status = 'rejected'
        join_request.processed_at = datetime.utcnow()
        join_request.processed_by = current_user.get('user_id')

        session.commit()

        return jsonify({'message': 'הבקשה נדחתה'}), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
        if current_user.get('role') != 'מפ' or current_user.get('pluga_id') is not None:
            return jsonify({'error': 'אין הרשאה'}), 403

        join_request = session.query(JoinRequest).filter_by(id=request_id).first()
        if not join_request:
            return jsonify({'error': 'בקשה לא נמצאה'}), 404

        session.delete(join_request)
        session.commit()

        return jsonify({'message': 'הבקשה נמחקה'}), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
    session = get_db()

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
                created_by=current_user.get('user_id'),
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

        # בדוק אם יש משימות בכלל לשיבוץ האוטומטי
        any_assignments = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id
        ).first()

        # אם אין משימות בכלל, נסה להריץ את אלגוריתם השיבוץ אוטומטית
        if not any_assignments:
            # בדוק אם יש תבניות משימות
            templates = session.query(AssignmentTemplate).filter_by(pluga_id=pluga_id).all()

            if templates and len(templates) > 0:
                # יש תבניות אבל אין משימות - נריץ את האלגוריתם אוטומטית
                print(f"🔄 מצאתי {len(templates)} תבניות משימות אבל אין משימות - מריץ שיבוץ אוטומטי...")

                try:
                    # הרץ את אלגוריתם השיבוץ באופן סינכרוני (פעם אחת בלבד)
                    # זה יכול לקחת כמה שניות, אבל זה קורה רק בפעם הראשונה
                    from assignment_logic import AssignmentLogic

                    # טעינת נתונים
                    pluga = session.query(Pluga).filter_by(id=pluga_id).first()
                    mahalkot = session.query(Mahlaka).filter_by(pluga_id=pluga_id).all()

                    # יצירת מבנה נתונים מלא (כמו ב-generate_shavzak)
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
                                UnavailableDate.date >= master_shavzak.start_date,
                                UnavailableDate.date < master_shavzak.start_date + timedelta(days=master_shavzak.days_count)
                            ).all()

                            unavailable_dates = [u.date for u in unavailable]

                            certifications = session.query(Certification).filter_by(soldier_id=soldier.id).all()
                            cert_list = [c.certification_name for c in certifications]

                            # קבל סטטוס נוכחי
                            status = session.query(SoldierStatus).filter_by(soldier_id=soldier.id).first()

                            soldier_data = {
                                'id': soldier.id,
                                'name': soldier.name,
                                'role': soldier.role,
                                'kita': soldier.kita,
                                'certifications': cert_list,
                                'unavailable_dates': unavailable_dates,
                                'hatash_2_days': soldier.hatash_2_days,
                                'status_type': status.status_type if status else 'בבסיס'
                            }

                            # מפקדים
                            if soldier.role in ['ממ', 'מכ', 'סמל']:
                                commanders.append(soldier_data)
                            # נהגים - גם ברשימת נהגים וגם כחיילים רגילים
                            if soldier.role == 'נהג':
                                drivers.append(soldier_data)
                            # כל מי שלא מפקד (כולל נהגים) - חיילים רגילים
                            if soldier.role not in ['ממ', 'מכ', 'סמל']:
                                regular_soldiers.append(soldier_data)

                        mahalkot_data.append({
                            'id': mahlaka.id,
                            'number': mahlaka.number,
                            'commanders': commanders,
                            'drivers': drivers,
                            'soldiers': regular_soldiers
                        })

                    # פונקציה לבדיקת זמינות חייל ביום מסוים
                    def is_soldier_available(soldier_data, check_date):
                        """בודק אם חייל זמין ביום מסוים, תוך התחשבות בהתש"ב 2 וריתוק"""
                        # אם החייל בריתוק, הוא לא זמין (ריתוק מבטל הכל)
                        if soldier_data.get('status_type') == 'ריתוק':
                            return False

                        # בדוק אם התאריך באי זמינות רגילה
                        if check_date in soldier_data.get('unavailable_dates', []):
                            return False

                        # בדוק התש"ב 2 - ימים קבועים שהחייל לא זמין
                        hatash_2_days = soldier_data.get('hatash_2_days')
                        if hatash_2_days:
                            day_of_week = check_date.weekday()  # 0=Monday, 6=Sunday
                            # התאם ל-0=Sunday כמו שמצפים בממשק
                            day_of_week = (day_of_week + 1) % 7
                            hatash_days_list = hatash_2_days.split(',')
                            if str(day_of_week) in hatash_days_list:
                                return False

                        return True

                    # אתחול אלגוריתם
                    logic = AssignmentLogic(
                        min_rest_hours=master_shavzak.min_rest_hours,
                        reuse_soldiers_for_standby=master_shavzak.reuse_soldiers_for_standby
                    )

                    # יצירת משימות עם אלגוריתם השיבוץ המלא
                    all_assignments = []
                    for day in range(min(master_shavzak.days_count, 7)):  # רק 7 ימים ראשונים
                        current_date = master_shavzak.start_date + timedelta(days=day)

                        for template in templates:
                            for slot in range(template.times_per_day):
                                # אם start_hour מוגדר בתבנית, השתמש בו. אחרת, חשב אוטומטית
                                if template.start_hour is not None:
                                    start_hour = template.start_hour + (slot * template.length_in_hours)
                                else:
                                    start_hour = slot * template.length_in_hours

                                # שם המשימה - ללא מספר סלוט! כל המשימות של אותה תבנית יוצגו באותה עמודה
                                # אבל בשורות שונות לפי שעת ההתחלה
                                assign_data = {
                                    'name': template.name,
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
                                    'reuse_soldiers_for_standby': template.reuse_soldiers_for_standby,
                                    'date': current_date
                                }

                                all_assignments.append(assign_data)

                    # מיון לפי יום ושעה, עם כוננויות אחרונות
                    def assignment_priority(assign):
                        is_standby = assign['type'] in ['כוננות א', 'כוננות ב']
                        priority = 1 if is_standby else 0
                        return (assign['day'], assign['start_hour'], priority)

                    all_assignments.sort(key=assignment_priority)

                    # הרצת השיבוץ עם אלגוריתם מלא
                    schedules = {}  # soldier_id -> [(day, start, end, name, type), ...]
                    mahlaka_workload = {m['id']: 0 for m in mahalkot_data}

                    # 🔧 תיקון: טען את כל המשימות הקיימות בשיבוץ האוטומטי (כולל ימים קודמים)
                    # זה קריטי כדי שהאלגוריתם יתחשב בהיסטוריה המלאה
                    existing_assignments_all = session.query(Assignment).filter(
                        Assignment.shavzak_id == master_shavzak.id
                    ).all()

                    print(f"🔄 טוען {len(existing_assignments_all)} משימות קיימות מהשיבוץ האוטומטי...")

                    # בנה את schedules מכל המשימות הקיימות (גם מימים קודמים)
                    for existing_assignment in existing_assignments_all:
                        # טען את החיילים שמשובצים למשימה הזו
                        soldiers_in_assignment = session.query(AssignmentSoldier).filter_by(
                            assignment_id=existing_assignment.id
                        ).all()

                        for soldier_assignment in soldiers_in_assignment:
                            soldier_id = soldier_assignment.soldier_id
                            if soldier_id not in schedules:
                                schedules[soldier_id] = []

                            # הוסף את המשימה ל-schedule של החייל
                            schedules[soldier_id].append((
                                existing_assignment.day,
                                existing_assignment.start_hour,
                                existing_assignment.start_hour + existing_assignment.length_in_hours,
                                existing_assignment.name,
                                existing_assignment.assignment_type
                            ))

                    # מחק משימות קיימות מהימים שאנחנו עומדים ליצור (כדי למנוע כפילויות)
                    days_to_create = set(range(min(master_shavzak.days_count, 7)))
                    assignments_to_delete = [a for a in existing_assignments_all if a.day in days_to_create]

                    if assignments_to_delete:
                        print(f"🗑️  מוחק {len(assignments_to_delete)} משימות קיימות מהימים שאנחנו עומדים ליצור...")
                        for assignment in assignments_to_delete:
                            # מחק את השיוכים
                            session.query(AssignmentSoldier).filter_by(assignment_id=assignment.id).delete()
                            session.delete(assignment)
                        session.commit()

                        # עדכן את schedules - הסר משימות שנמחקו
                        for soldier_id in list(schedules.keys()):
                            schedules[soldier_id] = [
                                s for s in schedules[soldier_id]
                                if s[0] not in days_to_create
                            ]

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
                                    if is_soldier_available(c, current_date)
                                ]
                                available_drivers = [
                                    d for d in mahlaka_info['drivers']
                                    if is_soldier_available(d, current_date)
                                ]
                                available_soldiers = [
                                    s for s in mahlaka_info['soldiers']
                                    if is_soldier_available(s, current_date)
                                ]

                                available_mahalkot.append({
                                    'id': mahlaka_info['id'],
                                    'number': mahlaka_info['number'],
                                    'commanders': available_commanders,
                                    'drivers': available_drivers,
                                    'soldiers': available_soldiers
                                })

                            available_commanders = [c for c in all_commanders if is_soldier_available(c, current_date)]
                            available_drivers = [d for d in all_drivers if is_soldier_available(d, current_date)]
                            available_soldiers = [s for s in all_soldiers if is_soldier_available(s, current_date)]

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
                                result = logic.assign_hafak_gashash(assign_data, available_soldiers, schedules)
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
                                    shavzak_id=master_shavzak.id,
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
                            error_msg = str(e)
                            failed_assignments.append((assign_data, error_msg))
                            print(f"🔴 שגיאה ביצירת שיבוץ: {error_msg}")
                            traceback.print_exc()

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
                                                     if is_soldier_available(c, current_date)],
                                        'drivers': [d for d in mahlaka_info['drivers']
                                                   if is_soldier_available(d, current_date)],
                                        'soldiers': [s for s in mahlaka_info['soldiers']
                                                    if is_soldier_available(s, current_date)]
                                    })

                                available_commanders = [c for c in all_commanders if is_soldier_available(c, current_date)]
                                available_drivers = [d for d in all_drivers if is_soldier_available(d, current_date)]
                                available_soldiers = [s for s in all_soldiers if is_soldier_available(s, current_date)]

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
                                    result = logic.assign_hafak_gashash(assign_data, available_soldiers, schedules)
                                elif assign_data['type'] == 'שלז':
                                    result = logic.assign_shalaz(assign_data, available_soldiers, schedules)
                                elif assign_data['type'] == 'קצין תורן':
                                    result = logic.assign_duty_officer(assign_data, available_commanders, schedules)

                                if result:
                                    assignment = Assignment(
                                        shavzak_id=master_shavzak.id,
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
                            except Exception as e2:
                                print(f"🔴 שגיאה גם במצב חירום: {str(e2)}")
                                traceback.print_exc()

                    session.commit()
                    print(f"✅ שיבוץ אוטומטי נוצר בהצלחה עם {len(all_assignments) - len(failed_assignments)}/{len(all_assignments)} משימות")

                except Exception as e:
                    session.rollback()
                    print(f"⚠️ שגיאה ביצירת שיבוץ ראשוני: {str(e)}")
                    traceback.print_exc()
            else:
                print(f"⚠️ אין תבניות משימות במערכת - לא ניתן להריץ שיבוץ אוטומטי")

        # בדוק אם יש משימות קיימות ליום המבוקש
        existing_assignments = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day == day_diff
        ).all()

        # אם יש משימות, החזר אותן
        if existing_assignments:
            pass  # נמשיך לבניית התגובה
        else:
            # אין משימות - החזר הודעה שאין שיבוץ ליום הזה
            return jsonify({
                'date': requested_date.isoformat(),
                'date_display': requested_date.strftime('%d/%m/%Y'),
                'day_index': day_diff,
                'assignments': [],
                'shavzak_id': master_shavzak.id,
                'info': 'לא קיים שיבוץ ליום זה. יש ליצור שיבוץ באמצעות אלגוריתם השיבוץ הראשי או להוסיף תבניות משימות.'
            }), 200

        # בנה תגובה
        assignments_data = []
        warnings = []  # אזהרות על בעיות בשיבוץ

        # מיון המשימות לפי שם (כדי שהאזהרות יהיו מסודרות)
        existing_assignments_sorted = sorted(existing_assignments, key=lambda a: a.name)

        for assignment in existing_assignments_sorted:
            # טען חיילים
            soldiers_in_assignment = session.query(AssignmentSoldier).filter(
                AssignmentSoldier.assignment_id == assignment.id
            ).all()

            soldiers_list = []
            commanders = 0
            drivers = 0
            regular_soldiers = 0

            for as_soldier in soldiers_in_assignment:
                soldier = session.get(Soldier, as_soldier.soldier_id)
                if soldier:
                    soldiers_list.append({
                        'id': soldier.id,
                        'name': soldier.name,
                        'role': soldier.role,
                        'role_in_assignment': as_soldier.role_in_assignment,
                        'mahlaka_id': soldier.mahlaka_id
                    })

                    # ספור לפי תפקיד
                    if as_soldier.role_in_assignment == 'מפקד':
                        commanders += 1
                    elif as_soldier.role_in_assignment == 'נהג':
                        drivers += 1
                    else:
                        regular_soldiers += 1

            # בדוק אזהרות למשימה זו
            # טען את התבנית המקורית אם קיימת
            # חלץ את שם התבנית מתוך שם המשימה (הסר מספרים בסוף)
            # למשל: "שמירה בוקר 2" -> "שמירה בוקר"
            template_name_match = re.match(r'^(.+?)\s+\d+$', assignment.name)
            template_name = template_name_match.group(1).strip() if template_name_match else assignment.name

            template = session.query(AssignmentTemplate).filter(
                AssignmentTemplate.pluga_id == pluga_id,
                AssignmentTemplate.name == template_name
            ).first()

            # אם לא מצאנו לפי שם, נסה לפי סוג (תאימות לאחור)
            if not template:
                template = session.query(AssignmentTemplate).filter(
                    AssignmentTemplate.pluga_id == pluga_id,
                    AssignmentTemplate.assignment_type == assignment.assignment_type
                ).first()

            if template:
                # חשב סך הכל חיילים שחסרים (טיפול ב-None)
                commanders_needed = template.commanders_needed or 0
                drivers_needed = template.drivers_needed or 0
                soldiers_needed = template.soldiers_needed or 0

                total_needed = commanders_needed + drivers_needed + soldiers_needed
                total_assigned = commanders + drivers + regular_soldiers
                missing_count = total_needed - total_assigned

                # בנה רשימת חסרים
                missing_parts = []
                if commanders_needed > commanders:
                    missing_parts.append(f"{commanders_needed - commanders} מפקדים")
                if drivers_needed > drivers:
                    missing_parts.append(f"{drivers_needed - drivers} נהגים")
                if soldiers_needed > regular_soldiers:
                    missing_parts.append(f"{soldiers_needed - regular_soldiers} לוחמים")

                if missing_parts:
                    message = f"⚠️ {assignment.name}: חסרים " + ", ".join(missing_parts)

                    # אם המשימה ריקה לחלוטין או חסרים יותר מ-50% - הצע למחוק
                    suggest_deletion = False
                    severity = "warning"

                    if total_assigned == 0:
                        severity = "critical"
                        suggest_deletion = True
                        suggestion = "המשימה ריקה לחלוטין. מומלץ למחוק אותה כדי לפנות משאבים."
                    elif missing_count >= total_needed * 0.5:
                        severity = "high"
                        suggest_deletion = True
                        suggestion = f"חסרים {missing_count} מתוך {total_needed} חיילים ({int(missing_count/total_needed*100)}%). מומלץ למחוק משימה זו."
                    else:
                        suggestion = None

                    warnings.append({
                        'message': message,
                        'assignment_id': assignment.id,
                        'assignment_name': assignment.name,
                        'severity': severity,
                        'suggest_deletion': suggest_deletion,
                        'suggestion': suggestion
                    })
            elif not soldiers_list:
                # אין תבנית ואין חיילים - זה מצב לא רגיל
                warnings.append({
                    'message': f"⚠️ {assignment.name}: אין חיילים משובצים",
                    'assignment_id': assignment.id,
                    'assignment_name': assignment.name,
                    'severity': 'warning',
                    'suggest_deletion': False,
                    'suggestion': None
                })

            assignments_data.append({
                'id': assignment.id,
                'name': assignment.name,
                'type': assignment.assignment_type,
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
            'shavzak_id': master_shavzak.id,
            'warnings': warnings
        }), 200

    except Exception as e:
        session.rollback()
        print(f"Error in live schedule: {str(e)}")
        traceback.print_exc()

        # נסה לנתח את השגיאה
        error_msg = str(e)
        detailed_error = 'שגיאה בטעינת שיבוץ חי'
        error_type = 'unknown_error'
        suggestions = []

        # נתח שגיאות נפוצות והוסף המלצות
        if 'created_by' in error_msg or 'user_id' in error_msg:
            detailed_error = 'שגיאה ביצירת שיבוץ אוטומטי - בעיית הרשאות משתמש'
            error_type = 'permission_error'
            suggestions.append('ודא שהמשתמש שלך קיים במערכת')
        elif 'no such column' in error_msg.lower():
            detailed_error = 'שגיאת מסד נתונים - חסרים שדות במסד הנתונים'
            error_type = 'database_schema_error'
            suggestions.append('יש לפנות למנהל המערכת לעדכון מסד הנתונים')
        elif 'foreign key' in error_msg.lower():
            detailed_error = 'שגיאת קשרים - אחד הנתונים (פלוגה או מחלקה) אינו תקין'
            error_type = 'foreign_key_error'
            suggestions.append('ודא שהפלוגה והמחלקות מוגדרות כראוי במערכת')
        elif 'pluga_id' in error_msg:
            detailed_error = 'שגיאה בזיהוי הפלוגה'
            error_type = 'pluga_error'
            suggestions.append('ודא שאתה משויך לפלוגה תקינה')
        elif 'NoneType' in error_msg:
            detailed_error = 'שגיאה בטעינת נתונים - אחד הנתונים הנדרשים חסר'
            error_type = 'missing_data_error'
            suggestions.append('ודא שכל הנתונים הבסיסיים (פלוגה, מחלקות, חיילים) מוגדרים במערכת')

        error_response = {
            'error': detailed_error,
            'error_type': error_type,
            'technical_details': error_msg
        }

        if suggestions:
            error_response['suggestions'] = suggestions

        return jsonify(error_response), 500
    finally:
        session.close()


@app.route('/api/plugot/<int:pluga_id>/live-schedule/regenerate', methods=['POST'])
@token_required
def regenerate_live_schedule(pluga_id, current_user):
    """
    מחק ויצור מחדש את השיבוץ האוטומטי
    שימושי כאשר משתנות תבניות משימות או מחלקות
    """
    session = get_db()

    try:
        # בדיקת הרשאות - רק מפקדים יכולים לבצע פעולה זו
        if not can_edit_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה לעדכן שיבוץ'}), 403

        # מצא את השיבוץ האוטומטי
        master_shavzak = session.query(Shavzak).filter(
            Shavzak.pluga_id == pluga_id,
            Shavzak.name == 'שיבוץ אוטומטי'
        ).first()

        if not master_shavzak:
            return jsonify({'error': 'לא נמצא שיבוץ אוטומטי'}), 404

        # מחק את כל המשימות הקיימות
        assignments = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id
        ).all()

        for assignment in assignments:
            # מחק את כל השיוכים של המשימה
            session.query(AssignmentSoldier).filter(
                AssignmentSoldier.assignment_id == assignment.id
            ).delete()
            # מחק את המשימה עצמה
            session.delete(assignment)

        session.commit()
        print(f"✅ נמחקו {len(assignments)} משימות מהשיבוץ האוטומטי")

        # עכשיו ייצור מחדש את השיבוץ בפעם הבאה שנטעין את הדף
        # (הקוד ב-get_live_schedule יזהה שאין משימות ויריץ את האלגוריתם אוטומטית)

        return jsonify({
            'success': True,
            'message': f'השיבוץ האוטומטי נמחק בהצלחה. {len(assignments)} משימות הוסרו.',
            'info': 'השיבוץ ייווצר מחדש אוטומטית בפעם הבאה שתיטען דף השיבוץ החי.'
        }), 200

    except Exception as e:
        session.rollback()
        print(f"Error in regenerate_live_schedule: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'שגיאה במחיקת השיבוץ: {str(e)}'}), 500
    finally:
        session.close()


# ============================================================================
# HELPER FUNCTIONS FOR SCHEDULE REGENERATION
# ============================================================================

def _trigger_schedule_regeneration(session, pluga_id):
    """
    מחיקת השיבוץ האוטומטי כדי לגרום ליצירה מחדש
    נקראת אוטומטית כאשר משתנות תבניות משימות או מחלקות
    """
    try:
        master_shavzak = session.query(Shavzak).filter(
            Shavzak.pluga_id == pluga_id,
            Shavzak.name == 'שיבוץ אוטומטי'
        ).first()

        if master_shavzak:
            # מחק את כל המשימות
            assignments = session.query(Assignment).filter(
                Assignment.shavzak_id == master_shavzak.id
            ).all()

            for assignment in assignments:
                session.query(AssignmentSoldier).filter(
                    AssignmentSoldier.assignment_id == assignment.id
                ).delete()
                session.delete(assignment)

            print(f"🔄 השיבוץ האוטומטי נמחק ({len(assignments)} משימות) - ייווצר מחדש בטעינה הבאה")
            return len(assignments)
        return 0
    except Exception as e:
        print(f"⚠️ שגיאה במחיקת השיבוץ האוטומטי: {str(e)}")
        # לא נעצור את התהליך - רק נדווח
        return 0


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
        print(f"🔴 Error deleting affected assignments: {str(e)}")
        traceback.print_exc()
        # לא נעצור את התהליך - רק נדווח


@app.route('/api/plugot/<int:pluga_id>/constraints', methods=['GET'])
@token_required
def get_constraints(pluga_id, current_user):
    """קבלת כל האילוצים של פלוגה"""
    session = get_db()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/plugot/<int:pluga_id>/constraints', methods=['POST'])
@token_required
@role_required(['מפ', 'ממ'])
def create_constraint(pluga_id, current_user):
    """יצירת אילוץ חדש"""
    session = get_db()
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
            created_by=current_user.get('user_id')
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/constraints/<int:constraint_id>', methods=['DELETE'])
@token_required
@role_required(['מפ', 'ממ'])
def delete_constraint(constraint_id, current_user):
    """מחיקת אילוץ"""
    session = get_db()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
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
    session = get_db()
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/soldiers/<int:soldier_id>/status', methods=['PUT'])
@token_required
def update_soldier_status(soldier_id, current_user):
    """עדכון סטטוס של חייל"""
    session = get_db()
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
        status.updated_by = current_user.get('user_id')
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
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/soldiers/<int:soldier_id>/exit-date', methods=['PUT'])
@token_required
def update_soldier_exit_date(soldier_id, current_user):
    """עדכון תאריך יציאה (סבב קו) של חייל - מעדכן גם UnavailableDate וגם SoldierStatus"""
    session = get_db()
    try:
        if not can_edit_soldier(current_user, soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        soldier = session.query(Soldier).get(soldier_id)
        if not soldier:
            return jsonify({'error': 'חייל לא נמצא'}), 404

        data = request.json
        exit_date_str = data.get('exit_date')

        if not exit_date_str:
            return jsonify({'error': 'חסר תאריך יציאה'}), 400

        # המרת תאריך (תמיכה בפורמטים שונים)
        try:
            # נסה DD.MM.YYYY
            exit_date = datetime.strptime(exit_date_str, '%d.%m.%Y').date()
        except ValueError:
            try:
                # נסה YYYY-MM-DD
                exit_date = datetime.strptime(exit_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'פורמט תאריך לא חוקי. השתמש ב-DD.MM.YYYY או YYYY-MM-DD'}), 400

        # עדכון/יצירת UnavailableDate
        unavailable = session.query(UnavailableDate).filter_by(
            soldier_id=soldier_id,
            date=exit_date
        ).first()

        if not unavailable:
            unavailable = UnavailableDate(
                soldier_id=soldier_id,
                date=exit_date
            )
            session.add(unavailable)

        # עדכון SoldierStatus
        status = session.query(SoldierStatus).filter_by(soldier_id=soldier_id).first()
        if not status:
            status = SoldierStatus(
                soldier_id=soldier_id,
                status_type='בסבב קו',
                return_date=exit_date
            )
            session.add(status)
        else:
            status.status_type = 'בסבב קו'
            status.return_date = exit_date

        status.updated_by = current_user.get('user_id')
        status.updated_at = datetime.now()

        session.commit()

        return jsonify({
            'message': 'תאריך יציאה עודכן בהצלחה',
            'exit_date': exit_date.isoformat(),
            'status': {
                'status_type': status.status_type,
                'return_date': status.return_date.isoformat() if status.return_date else None
            }
        }), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# SMART SCHEDULING (ML)
# ============================================================================

from smart_scheduler import SmartScheduler
import base64
from io import BytesIO

# אתחול המודל
ML_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ml_model.pkl')
smart_scheduler = SmartScheduler()

# נסה לטעון מודל קיים
if os.path.exists(ML_MODEL_PATH):
    smart_scheduler.load_model(ML_MODEL_PATH)
    print("✅ Smart Scheduler: מודל נטען מ-ml_model.pkl")
else:
    print("⚠️ Smart Scheduler: אין מודל קיים - יש לאמן תחילה")


@app.route('/api/ml/train', methods=['POST'])
@token_required
def ml_train(current_user):
    """
    אימון המודל ML מדוגמאות

    Body:
    {
        "examples": [
            {
                "assignments": [...],
                "rating": "excellent" | "good" | "bad"
            }
        ]
    }
    """
    try:
        data = request.get_json()
        examples = data.get('examples', [])

        if not examples:
            return jsonify({'error': 'לא סופקו דוגמאות לאימון'}), 400

        # אמן את המודל
        smart_scheduler.train_from_examples(examples)

        # שמור את המודל
        smart_scheduler.save_model(ML_MODEL_PATH)

        stats = smart_scheduler.get_stats()

        return jsonify({
            'message': f'המודל אומן בהצלחה מ-{len(examples)} דוגמאות',
            'stats': stats
        }), 200

    except Exception as e:
        print(f"🔴 שגיאה באימון ML: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/ml/smart-schedule', methods=['POST'])
@token_required
def ml_smart_schedule(current_user):
    """
    יצירת שיבוץ חכם עם ML

    Body:
    {
        "pluga_id": 1,
        "start_date": "2025-01-01",
        "days_count": 7
    }
    """
    session = get_session(engine)

    try:
        data = request.get_json()
        pluga_id = data.get('pluga_id')
        start_date_str = data.get('start_date')
        days_count = data.get('days_count', 7)

        # בדיקות
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה לפלוגה זו'}), 403

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        # טען נתונים
        mahalkot = session.query(Mahlaka).filter_by(pluga_id=pluga_id).all()
        templates = session.query(AssignmentTemplate).filter_by(pluga_id=pluga_id).all()

        if not templates:
            return jsonify({'error': 'אין תבניות משימות במערכת'}), 400

        # בנה מבנה נתונים
        mahalkot_data = []
        for mahlaka in mahalkot:
            soldiers = session.query(Soldier).filter_by(mahlaka_id=mahlaka.id).all()

            commanders = []
            drivers = []
            regular_soldiers = []

            for soldier in soldiers:
                unavailable = session.query(UnavailableDate).filter(
                    UnavailableDate.soldier_id == soldier.id,
                    UnavailableDate.date >= start_date,
                    UnavailableDate.date < start_date + timedelta(days=days_count)
                ).all()

                unavailable_dates = [u.date for u in unavailable]

                certifications = session.query(Certification).filter_by(soldier_id=soldier.id).all()
                cert_list = [c.certification_name for c in certifications]

                status = session.query(SoldierStatus).filter_by(soldier_id=soldier.id).first()

                soldier_data = {
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'kita': soldier.kita,
                    'certifications': cert_list,
                    'unavailable_dates': unavailable_dates,
                    'hatash_2_days': soldier.hatash_2_days,
                    'status_type': status.status_type if status else 'בבסיס',
                    'mahlaka_id': mahlaka.id
                }

                if soldier.role in ['ממ', 'מכ', 'סמל']:
                    commanders.append(soldier_data)
                if soldier.role == 'נהג' or 'נהג' in cert_list:
                    drivers.append(soldier_data)
                if soldier.role not in ['ממ', 'מכ', 'סמל']:
                    regular_soldiers.append(soldier_data)

            mahalkot_data.append({
                'id': mahlaka.id,
                'number': mahlaka.number,
                'commanders': commanders,
                'drivers': drivers,
                'soldiers': regular_soldiers
            })

        # פונקציה לבדיקת זמינות
        def is_soldier_available(soldier_data, check_date):
            if soldier_data.get('status_type') == 'ריתוק':
                return False

            if check_date in soldier_data.get('unavailable_dates', []):
                return False

            hatash_2_days = soldier_data.get('hatash_2_days')
            if hatash_2_days:
                day_of_week = check_date.weekday()
                day_of_week = (day_of_week + 1) % 7
                hatash_days_list = hatash_2_days.split(',')
                if str(day_of_week) in hatash_days_list:
                    return False

            return True

        # יצירת משימות
        all_assignments = []
        for day in range(days_count):
            current_date = start_date + timedelta(days=day)

            for template in templates:
                for slot in range(template.times_per_day):
                    if template.start_hour is not None:
                        start_hour = template.start_hour + (slot * template.length_in_hours)
                    else:
                        start_hour = slot * template.length_in_hours

                    assign_data = {
                        'name': template.name,
                        'type': template.assignment_type,
                        'day': day,
                        'start_hour': start_hour,
                        'length_in_hours': template.length_in_hours,
                        'commanders_needed': template.commanders_needed,
                        'drivers_needed': template.drivers_needed,
                        'soldiers_needed': template.soldiers_needed,
                        'same_mahlaka_required': template.same_mahlaka_required,
                        'requires_certification': template.requires_certification,
                        'date': current_date
                    }

                    all_assignments.append(assign_data)

        # מיון
        def assignment_priority(assign):
            is_standby = assign['type'] in ['כוננות א', 'כוננות ב']
            priority = 1 if is_standby else 0
            return (assign['day'], assign['start_hour'], priority)

        all_assignments.sort(key=assignment_priority)

        # הרצת ML
        schedules = {}
        mahlaka_workload = {m['id']: 0 for m in mahalkot_data}

        all_commanders = [c for m in mahalkot_data for c in m['commanders']]
        all_drivers = [d for m in mahalkot_data for d in m['drivers']]
        all_soldiers = [s for m in mahalkot_data for s in m['soldiers']]

        created_assignments = []

        failed_assignments = []  # עקוב אחר משימות שלא השתבצו

        for assign_data in all_assignments:
            current_date = assign_data['date']

            # סינון לפי זמינות
            available_commanders = [c for c in all_commanders if is_soldier_available(c, current_date)]
            available_drivers = [d for d in all_drivers if is_soldier_available(d, current_date)]
            available_soldiers = [s for s in all_soldiers if is_soldier_available(s, current_date)]

            all_available = available_commanders + available_drivers + available_soldiers

            # הרץ ML
            result = smart_scheduler.assign_task(assign_data, all_available, schedules, mahlaka_workload)

            if result:
                # עדכן schedules
                for role_key in ['commanders', 'drivers', 'soldiers']:
                    if role_key in result:
                        for soldier_id in result[role_key]:
                            if soldier_id not in schedules:
                                schedules[soldier_id] = []
                            schedules[soldier_id].append((
                                assign_data['day'],
                                assign_data['start_hour'],
                                assign_data['start_hour'] + assign_data['length_in_hours'],
                                assign_data['name'],
                                assign_data['type']
                            ))

                created_assignments.append({
                    **assign_data,
                    'result': result
                })
            else:
                # משימה לא השתבצה - שמור לדיווח
                failed_assignments.append(assign_data)
                print(f"❌ לא הצלחתי לשבץ: {assign_data['name']} ({assign_data['type']}) יום {assign_data['day']} שעה {assign_data['start_hour']}")

        smart_scheduler.stats['total_assignments'] += len(created_assignments)
        smart_scheduler.stats['successful_assignments'] += len(created_assignments)
        smart_scheduler.save_model(ML_MODEL_PATH)

        # הכן הודעה עם סטטוס
        total_attempted = len(all_assignments)
        success_count = len(created_assignments)
        failed_count = len(failed_assignments)

        message = f'נוצרו {success_count} משימות בהצלחה'
        if failed_count > 0:
            message += f' ({failed_count} משימות לא הצליחו להישבץ)'
            print(f"\n📊 סיכום: {success_count}/{total_attempted} משימות שובצו בהצלחה")
            print(f"⚠️  משימות שלא השתבצו:")
            for failed in failed_assignments:
                print(f"   - {failed['name']} ({failed['type']}) יום {failed['day']}")

        return jsonify({
            'message': message,
            'assignments': created_assignments,
            'stats': smart_scheduler.get_stats(),
            'failed_assignments': [
                {'name': f['name'], 'type': f['type'], 'day': f['day'], 'start_hour': f['start_hour']}
                for f in failed_assignments
            ],
            'success_rate': f"{(success_count / total_attempted * 100):.1f}%" if total_attempted > 0 else "0%"
        }), 200

    except Exception as e:
        print(f"🔴 שגיאה ביצירת שיבוץ חכם: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/ml/feedback', methods=['POST'])
@token_required
def ml_feedback(current_user):
    """
    הוספת פידבק על שיבוץ עם לולאת למידה אוטומטית

    Body:
    {
        "assignment_id": 123,
        "shavzak_id": 456,
        "rating": "approved" | "rejected" | "modified",
        "changes": {...},  // אופציונלי
        "enable_auto_regeneration": true  // האם להפעיל יצירה אוטומטית
    }
    """
    session = get_session(engine)

    try:
        data = request.get_json()

        # הדפס את הבקשה לדיבאג
        print(f"📥 ML Feedback request: {data}")

        assignment_id = data.get('assignment_id')
        shavzak_id = data.get('shavzak_id')
        rating = data.get('rating')
        changes = data.get('changes')
        enable_auto_regeneration = data.get('enable_auto_regeneration', True)

        # בדיקת שדות חובה - שימוש ב-is None במקום not כדי לאפשר 0
        if assignment_id is None:
            print(f"❌ חסר assignment_id: {data}")
            return jsonify({'error': 'חסר assignment_id', 'received_data': data}), 400
        if shavzak_id is None:
            print(f"❌ חסר shavzak_id: {data}")
            return jsonify({'error': 'חסר shavzak_id', 'received_data': data}), 400
        if not rating or rating not in ['approved', 'rejected', 'modified']:
            print(f"❌ rating לא תקין: {rating}, data: {data}")
            return jsonify({'error': 'rating לא תקין', 'received_rating': rating, 'expected': ['approved', 'rejected', 'modified']}), 400

        # טען משימה
        assignment = session.get(Assignment, assignment_id)
        if not assignment:
            return jsonify({'error': 'משימה לא נמצאה'}), 404

        # הוסף פידבק
        assignment_data = {
            'id': assignment.id,
            'type': assignment.assignment_type,
            'name': assignment.name,
            'day': assignment.day,
            'start_hour': assignment.start_hour,
            'length_in_hours': assignment.length_in_hours,
            'soldiers': [s.soldier_id for s in assignment.soldiers_assigned]
        }

        # שימוש בלולאת למידה
        result = smart_scheduler.add_feedback_with_learning_loop(
            shavzak_id=shavzak_id,
            assignment=assignment_data,
            rating=rating,
            changes=changes
        )

        # שמור את הפידבק במסד הנתונים
        from models import FeedbackHistory, ScheduleIteration

        # מצא או צור איטרציה
        iteration = session.query(ScheduleIteration).filter_by(
            shavzak_id=shavzak_id,
            is_active=True
        ).first()

        if not iteration:
            # צור איטרציה ראשונה
            last_iteration = session.query(ScheduleIteration).filter_by(
                shavzak_id=shavzak_id
            ).order_by(ScheduleIteration.iteration_number.desc()).first()

            iteration_number = last_iteration.iteration_number + 1 if last_iteration else 1

            iteration = ScheduleIteration(
                shavzak_id=shavzak_id,
                iteration_number=iteration_number,
                is_active=True,
                status='pending',
                created_by=current_user.get('user_id')
            )
            session.add(iteration)
            session.commit()

        # שמור את הפידבק
        feedback = FeedbackHistory(
            shavzak_id=shavzak_id,
            iteration_id=iteration.id,
            assignment_id=assignment_id,
            rating=rating,
            feedback_text=changes.get('feedback_text') if changes else None,
            changes=json.dumps(changes) if changes else None,
            user_id=current_user.get('user_id'),
            triggered_new_iteration=result['needs_regeneration']
        )
        session.add(feedback)

        # עדכן מצב האיטרציה
        if rating == 'approved':
            iteration.status = 'approved'
        elif rating == 'rejected':
            iteration.status = 'rejected'
            if result['needs_regeneration'] and enable_auto_regeneration:
                # הפוך את האיטרציה הנוכחית ללא פעילה
                iteration.is_active = False
                iteration.status = 'superseded'
        elif rating == 'modified':
            iteration.status = 'modified'

        session.commit()
        smart_scheduler.save_model(ML_MODEL_PATH)

        response = {
            'message': result['message'],
            'stats': smart_scheduler.get_stats(),
            'needs_regeneration': result['needs_regeneration'],
            'iteration_status': result['iteration_status'],
            'feedback_id': feedback.id,
            'iteration_id': iteration.id
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"🔴 שגיאה בהוספת פידבק: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/ml/regenerate-schedule', methods=['POST'])
@token_required
def ml_regenerate_schedule(current_user):
    """
    יצירת איטרציה חדשה של שיבוץ אחרי פידבק שלילי

    Body:
    {
        "shavzak_id": 123,
        "reason": "פידבק שלילי - יצירת שיבוץ משופר"
    }
    """
    session = get_session(engine)

    try:
        data = request.get_json()
        shavzak_id = data.get('shavzak_id')
        reason = data.get('reason', 'יצירת איטרציה חדשה')

        # טען שיבוץ
        from models import Shavzak, ScheduleIteration, Assignment, AssignmentSoldier
        shavzak = session.get(Shavzak, shavzak_id)
        if not shavzak:
            return jsonify({'error': 'שיבוץ לא נמצא'}), 404

        # בדוק הרשאות
        if not can_view_pluga(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה לשיבוץ זה'}), 403

        # מצא את האיטרציה האחרונה
        last_iteration = session.query(ScheduleIteration).filter_by(
            shavzak_id=shavzak_id
        ).order_by(ScheduleIteration.iteration_number.desc()).first()

        new_iteration_number = last_iteration.iteration_number + 1 if last_iteration else 1

        # צור איטרציה חדשה
        new_iteration = ScheduleIteration(
            shavzak_id=shavzak_id,
            iteration_number=new_iteration_number,
            is_active=True,
            status='pending',
            created_by=current_user.get('user_id')
        )
        session.add(new_iteration)

        # מחק את השיבוצים הישנים
        old_assignments = session.query(Assignment).filter_by(shavzak_id=shavzak_id).all()
        for assignment in old_assignments:
            # מחק קודם את AssignmentSoldier
            session.query(AssignmentSoldier).filter_by(assignment_id=assignment.id).delete()
            session.delete(assignment)

        session.commit()

        # כעת צור שיבוץ חדש עם ה-ML המשופר
        # השתמש באותו קוד של ml_smart_schedule
        from datetime import timedelta
        from models import Mahlaka, AssignmentTemplate, Soldier, UnavailableDate, Certification, SoldierStatus

        pluga_id = shavzak.pluga_id
        start_date = shavzak.start_date
        days_count = shavzak.days_count

        # טען נתונים
        mahalkot = session.query(Mahlaka).filter_by(pluga_id=pluga_id).all()
        templates = session.query(AssignmentTemplate).filter_by(pluga_id=pluga_id).all()

        if not templates:
            return jsonify({'error': 'אין תבניות משימות במערכת'}), 400

        # בנה מבנה נתונים
        mahalkot_data = []
        for mahlaka in mahalkot:
            soldiers = session.query(Soldier).filter_by(mahlaka_id=mahlaka.id).all()

            commanders = []
            drivers = []
            regular_soldiers = []

            for soldier in soldiers:
                unavailable = session.query(UnavailableDate).filter(
                    UnavailableDate.soldier_id == soldier.id,
                    UnavailableDate.date >= start_date,
                    UnavailableDate.date < start_date + timedelta(days=days_count)
                ).all()

                unavailable_dates = [u.date for u in unavailable]

                certifications = session.query(Certification).filter_by(soldier_id=soldier.id).all()
                cert_list = [c.certification_name for c in certifications]

                status = session.query(SoldierStatus).filter_by(soldier_id=soldier.id).first()

                soldier_data = {
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'kita': soldier.kita,
                    'certifications': cert_list,
                    'unavailable_dates': unavailable_dates,
                    'hatash_2_days': soldier.hatash_2_days,
                    'status_type': status.status_type if status else 'בבסיס',
                    'mahlaka_id': mahlaka.id
                }

                if soldier.role in ['ממ', 'מכ', 'סמל']:
                    commanders.append(soldier_data)
                if soldier.role == 'נהג' or 'נהג' in cert_list:
                    drivers.append(soldier_data)
                if soldier.role not in ['ממ', 'מכ', 'סמל']:
                    regular_soldiers.append(soldier_data)

            mahalkot_data.append({
                'id': mahlaka.id,
                'number': mahlaka.number,
                'commanders': commanders,
                'drivers': drivers,
                'soldiers': regular_soldiers
            })

        # פונקציה לבדיקת זמינות
        def is_soldier_available(soldier_data, check_date):
            if soldier_data.get('status_type') == 'ריתוק':
                return False

            if check_date in soldier_data.get('unavailable_dates', []):
                return False

            hatash_2_days = soldier_data.get('hatash_2_days')
            if hatash_2_days:
                day_of_week = check_date.weekday()
                day_of_week = (day_of_week + 1) % 7
                hatash_days_list = hatash_2_days.split(',')
                if str(day_of_week) in hatash_days_list:
                    return False

            return True

        # יצירת משימות
        all_assignments = []
        for day in range(days_count):
            current_date = start_date + timedelta(days=day)

            for template in templates:
                for slot in range(template.times_per_day):
                    if template.start_hour is not None:
                        start_hour = template.start_hour + (slot * template.length_in_hours)
                    else:
                        start_hour = slot * template.length_in_hours

                    assign_data = {
                        'name': template.name,
                        'type': template.assignment_type,
                        'day': day,
                        'start_hour': start_hour,
                        'length_in_hours': template.length_in_hours,
                        'commanders_needed': template.commanders_needed,
                        'drivers_needed': template.drivers_needed,
                        'soldiers_needed': template.soldiers_needed,
                        'same_mahlaka_required': template.same_mahlaka_required,
                        'requires_certification': template.requires_certification,
                        'date': current_date
                    }

                    all_assignments.append(assign_data)

        # מיון
        def assignment_priority(assign):
            is_standby = assign['type'] in ['כוננות א', 'כוננות ב']
            priority = 1 if is_standby else 0
            return (assign['day'], assign['start_hour'], priority)

        all_assignments.sort(key=assignment_priority)

        # הרצת ML (המודל למד מהפידבקים!)
        schedules = {}
        mahlaka_workload = {m['id']: 0 for m in mahalkot_data}

        all_commanders = [c for m in mahalkot_data for c in m['commanders']]
        all_drivers = [d for m in mahalkot_data for d in m['drivers']]
        all_soldiers = [s for m in mahalkot_data for s in m['soldiers']]

        created_assignments = []
        failed_assignments = []  # עקוב אחר משימות שלא השתבצו

        for assign_data in all_assignments:
            current_date = assign_data['date']

            # סינון לפי זמינות
            available_commanders = [c for c in all_commanders if is_soldier_available(c, current_date)]
            available_drivers = [d for d in all_drivers if is_soldier_available(d, current_date)]
            available_soldiers = [s for s in all_soldiers if is_soldier_available(s, current_date)]

            all_available = available_commanders + available_drivers + available_soldiers

            # הרץ ML (עם הלמידה החדשה!)
            result = smart_scheduler.assign_task(assign_data, all_available, schedules, mahlaka_workload)

            if result:
                # עדכן schedules
                for role_key in ['commanders', 'drivers', 'soldiers']:
                    if role_key in result:
                        for soldier_id in result[role_key]:
                            if soldier_id not in schedules:
                                schedules[soldier_id] = []
                            schedules[soldier_id].append((
                                assign_data['day'],
                                assign_data['start_hour'],
                                assign_data['start_hour'] + assign_data['length_in_hours'],
                                assign_data['name'],
                                assign_data['type']
                            ))

                # שמור את המשימה החדשה במסד הנתונים
                new_assignment = Assignment(
                    shavzak_id=shavzak_id,
                    name=assign_data['name'],
                    assignment_type=assign_data['type'],
                    day=assign_data['day'],
                    start_hour=assign_data['start_hour'],
                    length_in_hours=assign_data['length_in_hours'],
                    assigned_mahlaka_id=result.get('mahlaka_id')
                )
                session.add(new_assignment)
                session.flush()  # כדי לקבל את ה-ID

                # הוסף חיילים למשימה
                for role_key in ['commanders', 'drivers', 'soldiers']:
                    if role_key in result:
                        for soldier_id in result[role_key]:
                            role_name = 'מפקד' if role_key == 'commanders' else ('נהג' if role_key == 'drivers' else 'לוחם')
                            assignment_soldier = AssignmentSoldier(
                                assignment_id=new_assignment.id,
                                soldier_id=soldier_id,
                                role_in_assignment=role_name
                            )
                            session.add(assignment_soldier)

                created_assignments.append({
                    **assign_data,
                    'result': result
                })
            else:
                # משימה לא השתבצה - שמור לדיווח
                failed_assignments.append(assign_data)
                print(f"❌ לא הצלחתי לשבץ: {assign_data['name']} ({assign_data['type']}) יום {assign_data['day']} שעה {assign_data['start_hour']}")

        session.commit()

        smart_scheduler.stats['total_assignments'] += len(created_assignments)
        smart_scheduler.stats['successful_assignments'] += len(created_assignments)
        smart_scheduler.save_model(ML_MODEL_PATH)

        # הכן הודעה עם סטטוס
        total_attempted = len(all_assignments)
        success_count = len(created_assignments)
        failed_count = len(failed_assignments)

        message = f'✅ נוצרה איטרציה חדשה ({new_iteration_number}) עם {success_count} משימות'
        if failed_count > 0:
            message += f' ({failed_count} משימות לא הצליחו להישבץ)'
            print(f"\n📊 סיכום איטרציה {new_iteration_number}: {success_count}/{total_attempted} משימות שובצו")
            print(f"⚠️  משימות שלא השתבצו:")
            for failed in failed_assignments:
                print(f"   - {failed['name']} ({failed['type']}) יום {failed['day']}")

        return jsonify({
            'message': message,
            'iteration_id': new_iteration.id,
            'iteration_number': new_iteration_number,
            'assignments_count': success_count,
            'stats': smart_scheduler.get_stats(),
            'reason': reason,
            'failed_assignments': [
                {'name': f['name'], 'type': f['type'], 'day': f['day'], 'start_hour': f['start_hour']}
                for f in failed_assignments
            ],
            'success_rate': f"{(success_count / total_attempted * 100):.1f}%" if total_attempted > 0 else "0%"
        }), 200

    except Exception as e:
        print(f"🔴 שגיאה ביצירת איטרציה חדשה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/ml/feedback-history/<int:shavzak_id>', methods=['GET'])
@token_required
def ml_feedback_history(current_user, shavzak_id):
    """
    קבלת היסטוריית פידבקים ואיטרציות לשיבוץ

    Returns:
    {
        "iterations": [
            {
                "id": 1,
                "iteration_number": 1,
                "status": "approved",
                "is_active": false,
                "created_at": "2025-01-01T10:00:00",
                "feedbacks": [...]
            }
        ],
        "current_iteration": {...},
        "total_feedbacks": 5
    }
    """
    session = get_session(engine)

    try:
        from models import Shavzak, ScheduleIteration, FeedbackHistory

        # טען שיבוץ
        shavzak = session.get(Shavzak, shavzak_id)
        if not shavzak:
            return jsonify({'error': 'שיבוץ לא נמצא'}), 404

        # בדוק הרשאות
        if not can_view_pluga(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה לשיבוץ זה'}), 403

        # טען את כל האיטרציות
        iterations = session.query(ScheduleIteration).filter_by(
            shavzak_id=shavzak_id
        ).order_by(ScheduleIteration.iteration_number).all()

        iterations_data = []
        current_iteration = None

        for iteration in iterations:
            # טען פידבקים לאיטרציה
            feedbacks = session.query(FeedbackHistory).filter_by(
                iteration_id=iteration.id
            ).order_by(FeedbackHistory.created_at).all()

            feedbacks_data = []
            for feedback in feedbacks:
                feedbacks_data.append({
                    'id': feedback.id,
                    'rating': feedback.rating,
                    'feedback_text': feedback.feedback_text,
                    'changes': json.loads(feedback.changes) if feedback.changes else None,
                    'user_id': feedback.user_id,
                    'created_at': feedback.created_at.isoformat(),
                    'triggered_new_iteration': feedback.triggered_new_iteration
                })

            iteration_data = {
                'id': iteration.id,
                'iteration_number': iteration.iteration_number,
                'status': iteration.status,
                'is_active': iteration.is_active,
                'created_at': iteration.created_at.isoformat(),
                'feedbacks': feedbacks_data,
                'feedbacks_count': len(feedbacks_data)
            }

            iterations_data.append(iteration_data)

            if iteration.is_active:
                current_iteration = iteration_data

        # סך כל הפידבקים
        total_feedbacks = session.query(FeedbackHistory).filter_by(
            shavzak_id=shavzak_id
        ).count()

        return jsonify({
            'iterations': iterations_data,
            'current_iteration': current_iteration,
            'total_iterations': len(iterations_data),
            'total_feedbacks': total_feedbacks
        }), 200

    except Exception as e:
        print(f"🔴 שגיאה בקבלת היסטוריית פידבקים: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/ml/stats', methods=['GET'])
@token_required
def ml_stats(current_user):
    """קבלת סטטיסטיקות ML"""
    try:
        stats = smart_scheduler.get_stats()
        return jsonify({
            'stats': stats,
            'model_loaded': os.path.exists(ML_MODEL_PATH)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ml/upload-example', methods=['POST'])
@token_required
def ml_upload_example(current_user):
    """
    העלאת דוגמת שיבוץ מתמונה

    Body:
    {
        "image": "base64_encoded_image",
        "rating": "excellent" | "good" | "bad"
    }
    """
    try:
        data = request.get_json()
        image_b64 = data.get('image')
        rating = data.get('rating', 'good')

        if not image_b64:
            return jsonify({'error': 'לא סופקה תמונה'}), 400

        # TODO: נוסיף OCR/ניתוח תמונה בעתיד
        # כרגע נחזיר הודעה שהתמונה נשמרה

        return jsonify({
            'message': 'תמונה התקבלה - ניתוח ידני נדרש כרגע',
            'note': 'בעתיד נוסיף OCR אוטומטי'
        }), 200

    except Exception as e:
        print(f"🔴 שגיאה בהעלאת דוגמה: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


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
