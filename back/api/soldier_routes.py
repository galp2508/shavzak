"""
Soldier Routes Blueprint
נתבי חיילים, הסמכות, אי-זמינות וסטטוסים
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import traceback

from models import (
    Soldier, Certification, UnavailableDate, Mahlaka,
    SoldierStatus, Shavzak, Assignment, AssignmentSoldier,
    AVAILABLE_ROLES_CERTIFICATIONS
)
from auth import (
    token_required, role_required,
    can_edit_mahlaka, can_view_mahlaka, can_edit_soldier
)
from .utils import get_db

soldier_bp = Blueprint('soldier', __name__)


# ============================================================================
# SOLDIER
# ============================================================================

@soldier_bp.route('/api/soldiers', methods=['POST'])
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

        # הוסף הסמכות שנבחרו על ידי המשתמש
        certifications_to_add = data.get('certifications', [])

        # אם החייל הוא מפקד (ממ, מכ, סמל), הוסף אוטומטית הסמכת "מפקד"
        commander_roles = ['ממ', 'מכ', 'סמל']
        if soldier.role in commander_roles and 'מפקד' not in certifications_to_add:
            certifications_to_add.append('מפקד')

        # הוסף את כל ההסמכות
        for cert_name in certifications_to_add:
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


@soldier_bp.route('/api/soldiers/bulk', methods=['POST'])
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

                # Parse dates
                if soldier_data.get('recruit_date'):
                    soldier.recruit_date = datetime.strptime(soldier_data['recruit_date'], '%Y-%m-%d').date()
                if soldier_data.get('birth_date'):
                    soldier.birth_date = datetime.strptime(soldier_data['birth_date'], '%Y-%m-%d').date()
                if soldier_data.get('home_round_date'):
                    soldier.home_round_date = datetime.strptime(soldier_data['home_round_date'], '%Y-%m-%d').date()

                session.add(soldier)
                session.flush()

                # הוסף הסמכות שנבחרו על ידי המשתמש
                certifications_to_add = soldier_data.get('certifications', [])

                # אם החייל הוא מפקד (ממ, מכ, סמל), הוסף אוטומטית הסמכת "מפקד"
                commander_roles = ['ממ', 'מכ', 'סמל']
                if soldier.role in commander_roles and 'מפקד' not in certifications_to_add:
                    certifications_to_add.append('מפקד')

                # הוסף את כל ההסמכות
                for cert_name in certifications_to_add:
                    cert = Certification(soldier_id=soldier.id, certification_name=cert_name)
                    session.add(cert)

                # Add unavailable date if provided
                if soldier_data.get('unavailable_date'):
                    date_str = soldier_data['unavailable_date']
                    try:
                        # Try DD.MM.YYYY format
                        unavailable_date = datetime.strptime(date_str, '%d.%m.%Y').date()
                    except ValueError:
                        try:
                            # Try YYYY-MM-DD format
                            unavailable_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except ValueError:
                            # Skip if invalid format
                            pass
                        else:
                            unavailable = UnavailableDate(
                                soldier_id=soldier.id,
                                date=unavailable_date,
                                reason='יציאה',
                                status='approved'
                            )
                            session.add(unavailable)
                    else:
                        unavailable = UnavailableDate(
                            soldier_id=soldier.id,
                            date=unavailable_date,
                            reason='יציאה',
                            status='approved'
                        )
                        session.add(unavailable)

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
            'message': f'נוצרו {len(created)} חיילים',
            'success_count': len(created),
            'created': created,
            'errors': errors
        }), 201 if created else 400
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@soldier_bp.route('/api/soldiers/<int:soldier_id>', methods=['GET'])
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
        cert_list = [{'id': cert.id, 'name': cert.certification_name} for cert in certifications]

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


@soldier_bp.route('/api/soldiers/<int:soldier_id>', methods=['PUT'])
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

        # אם התפקיד השתנה למפקד, ודא שיש לו הסמכת "מפקד"
        commander_roles = ['ממ', 'מכ', 'סמל']
        if soldier.role in commander_roles:
            # בדוק אם יש לו כבר הסמכת "מפקד"
            existing_commander_cert = session.query(Certification).filter(
                Certification.soldier_id == soldier.id,
                Certification.certification_name == 'מפקד'
            ).first()

            # אם אין לו הסמכת "מפקד", הוסף אותה
            if not existing_commander_cert:
                commander_cert = Certification(soldier_id=soldier.id, certification_name='מפקד')
                session.add(commander_cert)

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


@soldier_bp.route('/api/soldiers/<int:soldier_id>', methods=['DELETE'])
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


@soldier_bp.route('/api/mahalkot/<int:mahlaka_id>/soldiers', methods=['GET'])
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
            cert_list = [{'id': cert.id, 'name': cert.certification_name} for cert in certifications]

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


# ============================================================================
# CERTIFICATIONS
# ============================================================================

@soldier_bp.route('/api/soldiers/<int:soldier_id>/certifications', methods=['POST'])
@token_required
def add_certification(soldier_id, current_user):
    """
    הוספת הסמכה (תפקיד נוסף) לחייל

    הסמכה = תפקיד נוסף שחייל יכול למלא במשימות
    לדוגמה: לוחם עם הסמכת "נהג" יכול לשמש כנהג במשימות
    """
    try:
        session = get_db()

        if not can_edit_soldier(current_user, soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json
        cert_name = data.get('certification_name', '').strip()

        # ולידציה: ודא שההסמכה היא מהרשימה המאושרת
        if cert_name not in AVAILABLE_ROLES_CERTIFICATIONS:
            return jsonify({
                'error': f'הסמכה לא תקינה. בחר מהרשימה: {", ".join(AVAILABLE_ROLES_CERTIFICATIONS)}'
            }), 400

        # בדוק אם כבר יש הסמכה כזו לחייל
        existing = session.query(Certification).filter(
            Certification.soldier_id == soldier_id,
            Certification.certification_name == cert_name
        ).first()

        if existing:
            return jsonify({'error': f'לחייל כבר יש הסמכת "{cert_name}"'}), 400

        cert = Certification(
            soldier_id=soldier_id,
            certification_name=cert_name
        )

        session.add(cert)
        session.flush()  # Ensure ID is populated before accessing
        session.commit()

        return jsonify({
            'message': f'הסמכת "{cert_name}" נוספה בהצלחה',
            'certification': {
                'id': cert.id,
                'name': cert.certification_name,
                'date_acquired': cert.date_acquired.isoformat()
            }
        }), 201
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@soldier_bp.route('/api/available-roles-certifications', methods=['GET'])
def get_available_roles_certifications():
    """
    קבלת רשימת התפקידים/הסמכות הזמינים במערכת

    הסמכה = תפקיד נוסף שחייל יכול למלא במשימות
    """
    return jsonify({
        'roles_certifications': AVAILABLE_ROLES_CERTIFICATIONS,
        'description': 'הסמכה = תפקיד נוסף שחייל יכול למלא במשימות'
    }), 200


@soldier_bp.route('/api/certifications/<int:certification_id>', methods=['DELETE'])
@token_required
def delete_certification(certification_id, current_user):
    """מחיקת הסמכה"""
    try:
        session = get_db()

        # מצא את ההסמכה
        cert = session.get(Certification, certification_id)
        if not cert:
            return jsonify({'error': 'הסמכה לא נמצאה'}), 404

        # בדוק הרשאות - רק מפקדים יכולים למחוק הסמכות
        if not can_edit_soldier(current_user, cert.soldier_id, session):
            return jsonify({'error': 'אין לך הרשאה למחוק הסמכה זו'}), 403

        # מנע מחיקת הסמכת "מפקד" ממפקדים
        soldier = session.query(Soldier).filter_by(id=cert.soldier_id).first()
        commander_roles = ['ממ', 'מכ', 'סמל']
        if soldier and soldier.role in commander_roles and cert.certification_name == 'מפקד':
            return jsonify({
                'error': 'לא ניתן למחוק הסמכת "מפקד" ממפקד. הסמכה זו ניתנת אוטומטית לכל מפקד.'
            }), 400

        cert_name = cert.certification_name
        session.delete(cert)
        session.commit()

        return jsonify({'message': f'הסמכת "{cert_name}" נמחקה בהצלחה'}), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# UNAVAILABLE DATES
# ============================================================================

@soldier_bp.route('/api/soldiers/<int:soldier_id>/unavailable', methods=['POST'])
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


@soldier_bp.route('/api/unavailable/<int:unavailable_id>', methods=['DELETE'])
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
# SOLDIER STATUS
# ============================================================================

@soldier_bp.route('/api/soldiers/<int:soldier_id>/status', methods=['GET'])
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


@soldier_bp.route('/api/soldiers/<int:soldier_id>/status', methods=['PUT'])
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


@soldier_bp.route('/api/soldiers/<int:soldier_id>/exit-date', methods=['PUT'])
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
