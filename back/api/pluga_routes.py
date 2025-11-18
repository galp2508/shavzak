"""
Pluga, Mahlaka, Assignment Templates, Constraints & Join Requests Routes
נתבי פלוגות, מחלקות, תבניות משימות, אילוצים ובקשות הצטרפות
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import traceback

from models import (
    Pluga, Mahlaka, User, Soldier, AssignmentTemplate,
    SchedulingConstraint, JoinRequest, Shavzak, Assignment,
    AssignmentSoldier
)
from auth import (
    token_required, role_required, can_edit_pluga, can_view_pluga,
    can_edit_mahlaka, can_view_mahlaka
)
from .utils import get_db, build_user_response

pluga_bp = Blueprint('pluga', __name__)


# ============================================================================
# PLUGA
# ============================================================================

@pluga_bp.route('/api/plugot', methods=['POST'])
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


@pluga_bp.route('/api/plugot', methods=['GET'])
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


@pluga_bp.route('/api/plugot/<int:pluga_id>', methods=['GET'])
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

@pluga_bp.route('/api/mahalkot', methods=['POST'])
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


@pluga_bp.route('/api/mahalkot/<int:mahlaka_id>', methods=['PUT'])
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


@pluga_bp.route('/api/mahalkot/<int:mahlaka_id>', methods=['DELETE'])
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

        return jsonify({'message': 'מחלקה נמחקה בהצלחה'}), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@pluga_bp.route('/api/mahalkot/bulk', methods=['POST'])
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
            'message': f'נוצרו {len(created)} מחלקות',
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


@pluga_bp.route('/api/plugot/<int:pluga_id>/mahalkot', methods=['GET'])
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
# ASSIGNMENT TEMPLATES
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


@pluga_bp.route('/api/plugot/<int:pluga_id>/assignment-templates', methods=['POST'])
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


@pluga_bp.route('/api/plugot/<int:pluga_id>/assignment-templates', methods=['GET'])
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


@pluga_bp.route('/api/assignment-templates/<int:template_id>', methods=['PUT'])
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


@pluga_bp.route('/api/assignment-templates/<int:template_id>', methods=['DELETE'])
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


@pluga_bp.route('/api/assignment-templates/<int:template_id>/duplicate', methods=['POST'])
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
            query = query.filter(Assignment.assignment_type == constraint.assignment_type)

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


@pluga_bp.route('/api/plugot/<int:pluga_id>/constraints', methods=['GET'])
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


@pluga_bp.route('/api/plugot/<int:pluga_id>/constraints', methods=['POST'])
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


@pluga_bp.route('/api/constraints/<int:constraint_id>', methods=['DELETE'])
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


@pluga_bp.route('/api/plugot/<int:pluga_id>/recent-assignments', methods=['GET'])
@token_required
def get_recent_assignments(pluga_id, current_user):
    """קבלת משימות אחרונות מהשיבוץ האוטומטי (לצורך פידבק על אילוצים)"""
    session = get_db()
    try:
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        # מצא את השיבוץ האוטומטי
        master_shavzak = session.query(Shavzak).filter(
            Shavzak.pluga_id == pluga_id,
            Shavzak.name == 'שיבוץ אוטומטי'
        ).first()

        if not master_shavzak:
            return jsonify({'assignments': []}), 200

        # טען משימות מ-14 הימים האחרונים
        today = datetime.now().date()
        start_of_period = today - timedelta(days=14)
        days_from_start = (today - master_shavzak.start_date).days

        assignments = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day >= max(0, (start_of_period - master_shavzak.start_date).days),
            Assignment.day <= days_from_start
        ).order_by(Assignment.day.desc(), Assignment.start_hour.desc()).limit(100).all()

        assignments_data = []
        for assignment in assignments:
            # חשב תאריך בפועל
            assignment_date = master_shavzak.start_date + timedelta(days=assignment.day)

            soldiers_data = []
            for soldier_assignment in assignment.soldiers_assigned:
                soldier = soldier_assignment.soldier
                soldiers_data.append({
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier_assignment.role_in_assignment
                })

            assignments_data.append({
                'id': assignment.id,
                'name': assignment.name,
                'assignment_type': assignment.assignment_type,
                'date': assignment_date.isoformat(),
                'day': assignment.day,
                'start_hour': assignment.start_hour,
                'length_in_hours': assignment.length_in_hours,
                'soldiers': soldiers_data
            })

        return jsonify({'assignments': assignments_data}), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# JOIN REQUESTS
# ============================================================================

@pluga_bp.route('/api/join-requests', methods=['GET'])
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


@pluga_bp.route('/api/join-requests/<int:request_id>/approve', methods=['POST'])
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


@pluga_bp.route('/api/join-requests/<int:request_id>/reject', methods=['POST'])
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


@pluga_bp.route('/api/join-requests/<int:request_id>', methods=['DELETE'])
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
