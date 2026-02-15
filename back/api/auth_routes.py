"""
Authentication Routes Blueprint
נתבי אימות והרשאות
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import traceback

from models import User, Pluga, JoinRequest
from auth import create_token, token_required, role_required
from .utils import get_db, build_user_response, limiter
from validation import validate_data, UserRegistrationSchema, UserLoginSchema
from ditto_client import ditto

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    """רישום משתמש חדש / בקשת הצטרפות"""
    session = None
    try:
        # אימות נתונים
        validated_data, errors = validate_data(UserRegistrationSchema, request.json)
        if errors:
            return jsonify({'errors': errors}), 400

        data = validated_data
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

            # Sync to Ditto
            try:
                ditto.upsert("users", {
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role,
                    "pluga_id": user.pluga_id,
                    "type": "user",
                    "_id": user.username
                })
            except Exception as e:
                print(f"⚠️ Failed to sync user to Ditto: {e}")

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

                # Sync to Ditto
                try:
                    ditto.upsert("join_requests", {
                        "username": join_request.username,
                        "full_name": join_request.full_name,
                        "pluga_name": join_request.pluga_name,
                        "gdud": join_request.gdud,
                        "status": "pending",
                        "type": "join_request",
                        "_id": join_request.username
                    })
                except Exception as e:
                    print(f"⚠️ Failed to sync join_request to Ditto: {e}")

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

                # Sync to Ditto
                try:
                    ditto.upsert("users", {
                        "username": user.username,
                        "full_name": user.full_name,
                        "role": user.role,
                        "pluga_id": user.pluga_id,
                        "type": "user",
                        "_id": user.username
                    })
                except Exception as e:
                    print(f"⚠️ Failed to sync user to Ditto: {e}")

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
        if session:
            session.close()


@auth_bp.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """התחברות - מוגבל ל-5 ניסיונות בדקה למניעת brute-force"""
    session = None
    try:
        # אימות נתונים
        validated_data, errors = validate_data(UserLoginSchema, request.json)
        if errors:
            return jsonify({'errors': errors}), 400

        data = validated_data
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
        if session:
            session.close()


@auth_bp.route('/api/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """קבלת פרטי המשתמש הנוכחי"""
    session = None
    try:
        session = get_db()
        user = session.query(User).filter_by(id=current_user.id).first()
        
        if not user:
            return jsonify({'error': 'משתמש לא נמצא'}), 404
            
        return jsonify({
            'user': build_user_response(user)
        })
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()


@auth_bp.route('/api/me', methods=['PUT'])
@token_required
def update_current_user(current_user):
    """עדכון פרטי המשתמש הנוכחי"""
    session = None
    try:
        data = request.json
        session = get_db()
        user = session.query(User).filter_by(id=current_user.id).first()

        if not user:
            return jsonify({'error': 'משתמש לא נמצא'}), 404

        # Update fields if provided
        if 'full_name' in data and data['full_name']:
            user.full_name = data['full_name']
        
        if 'username' in data and data['username'] and data['username'] != user.username:
            # Check if username exists
            existing = session.query(User).filter(User.username == data['username'], User.id != user.id).first()
            if existing:
                return jsonify({'error': 'שם המשתמש כבר קיים במערכת'}), 400
            user.username = data['username']

        if 'password' in data and data['password']:
            user.set_password(data['password'])

        session.commit()

        # Generate new token
        token = create_token(user)

        # Sync to Ditto
        try:
            ditto.upsert("users", {
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "pluga_id": user.pluga_id,
                "type": "user",
                "_id": user.username
            })
        except Exception as e:
            print(f"⚠️ Failed to sync user to Ditto: {e}")

        return jsonify({
            'message': 'פרטי המשתמש עודכנו בהצלחה',
            'token': token,
            'user': build_user_response(user)
        })

    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        try:
            session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()



@auth_bp.route('/api/users', methods=['POST'])
@token_required
@role_required(['מפ', 'ממ'])
def create_user(current_user):
    """יצירת משתמש"""
    session = None
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
        if session:
            session.close()
