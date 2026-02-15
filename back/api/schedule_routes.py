"""
Schedule Routes Blueprint
כל ה-routes הקשורים לשיבוצים, משימות, ולוח זמנים חי
"""
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, timedelta
import traceback
import re
import csv
import io

from models import (
    get_session, Shavzak, Assignment, AssignmentSoldier, Pluga, Mahlaka,
    Soldier, UnavailableDate, Certification, AssignmentTemplate,
    SoldierStatus, SchedulingConstraint
)
from sqlalchemy.orm import joinedload, selectinload
from auth import (
    token_required, role_required,
    can_create_shavzak, can_view_shavzak, can_view_pluga, can_edit_pluga,
    can_edit_mahlaka
)
from .utils import get_db, build_user_response
from smart_scheduler import SmartScheduler
import os
from ditto_client import ditto

schedule_bp = Blueprint('schedule', __name__)

# אתחול המודל ML (shared with ml_routes)
ML_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_model.pkl')
smart_scheduler = SmartScheduler()

# נסה לטעון מודל קיים
if os.path.exists(ML_MODEL_PATH):
    smart_scheduler.load_model(ML_MODEL_PATH)
    print("✅ Smart Scheduler (schedule_bp): מודל נטען מ-ml_model.pkl")
else:
    print("⚠️ Smart Scheduler (schedule_bp): אין מודל קיים - יש לאמן תחילה")


# ============================================================================
# SHAVZAKIM - ניהול שיבוצים
# ============================================================================

@schedule_bp.route('/api/shavzakim', methods=['POST'])
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

        # Sync to Ditto
        try:
            shavzak_data = {
                "pluga_id": shavzak.pluga_id,
                "name": shavzak.name,
                "start_date": shavzak.start_date.isoformat(),
                "days_count": shavzak.days_count,
                "created_by": shavzak.created_by,
                "min_rest_hours": shavzak.min_rest_hours,
                "emergency_mode": shavzak.emergency_mode,
                "type": "shavzak",
                "_id": str(shavzak.id)
            }
            ditto.upsert("shavzakim", shavzak_data)
        except Exception as e:
            print(f"⚠️ Failed to sync shavzak to Ditto: {e}")

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


@schedule_bp.route('/api/shavzakim/<int:shavzak_id>/generate', methods=['POST'])
@token_required
def generate_shavzak(shavzak_id, current_user):
    """הרצת אלגוריתם השיבוץ המלא"""
    try:
        session = get_db()

        # Lock the shavzak row to prevent concurrent generation race conditions
        shavzak = session.query(Shavzak).filter_by(id=shavzak_id).with_for_update().first()
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

        # יצירת מבנה נתונים - אופטימיזציה: טעינה מקדימה של כל הנתונים
        # 🚀 תיקון ביצועים: טוען את כל החיילים עם כל הנתונים הקשורים בשאילתה אחת!
        all_soldiers_query = session.query(Soldier).options(
            selectinload(Soldier.certifications),
            selectinload(Soldier.unavailable_dates),
            selectinload(Soldier.current_status)
        ).join(Mahlaka).filter(Mahlaka.pluga_id == pluga.id).all()

        # בנה מילון מהיר לפי mahlaka_id
        soldiers_by_mahlaka = {}
        for soldier in all_soldiers_query:
            if soldier.mahlaka_id not in soldiers_by_mahlaka:
                soldiers_by_mahlaka[soldier.mahlaka_id] = []
            soldiers_by_mahlaka[soldier.mahlaka_id].append(soldier)

        mahalkot_data = []
        for mahlaka in mahalkot:
            soldiers = soldiers_by_mahlaka.get(mahlaka.id, [])

            commanders = []
            drivers = []
            regular_soldiers = []

            for soldier in soldiers:
                # 🚀 בדיקת זמינות - נתונים כבר טעונים!
                unavailable_dates = [
                    u.date for u in soldier.unavailable_dates
                    if u.date >= shavzak.start_date and u.date < shavzak.start_date + timedelta(days=shavzak.days_count)
                ]

                cert_list = [c.certification_name for c in soldier.certifications]
                status = soldier.current_status

                soldier_data = {
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'kita': soldier.kita,
                    'certifications': cert_list,
                    'unavailable_dates': unavailable_dates,
                    'hatash_2_days': soldier.hatash_2_days,
                    'home_round_date': soldier.home_round_date,
                    'status_type': status.status_type if status else 'בבסיס',
                    'status_end_date': status.end_date if status else None,
                    'status_return_date': status.return_date if status else None,
                    'mahlaka_id': mahlaka.id,  # חשוב ל-ML!
                    'mahlaka_is_special': mahlaka.is_special
                }

                # כל חייל מופיע רק ברשימה אחת
                if soldier.role in ['ממ', 'מכ', 'סמל']:
                    commanders.append(soldier_data)
                elif 'נהג' in cert_list:
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
            """בודק אם חייל זמין ביום מסוים, תוך התחשבות בנוכחות, התש"ב 2 וסטטוס"""
            # בדוק סטטוס החייל - חיילים שלא בבסיס לא זמינים
            status_type = soldier_data.get('status_type', 'בבסיס')

            # רשימת סטטוסים שמונעים שיבוץ
            unavailable_statuses = ['ריתוק', 'לא בבסיס', 'חופשה', 'מילואים', 'גימלים', 'בסבב קו', 'בקשת יציאה', 'מיוחדת']

            if status_type in unavailable_statuses:
                # בדוק אם הסטטוס רלוונטי לתאריך הנבדק
                status_end = soldier_data.get('status_end_date') or soldier_data.get('status_return_date')
                
                # אם אין תאריך סיום, הסטטוס תקף תמיד (עד שישונה ידנית)
                # אם יש תאריך סיום, בדוק אם התאריך הנבדק הוא לפני תאריך הסיום
                if not status_end or check_date <= status_end:
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

            # בדוק סבב יציאה (אם מוגדר)
            # אם תאריך סבב היציאה מוגדר, נחשב אם החייל בבית או בסבב קו
            home_round_date = soldier_data.get('home_round_date')
            if home_round_date:
                if isinstance(home_round_date, str):
                    home_round_date = datetime.strptime(home_round_date, '%Y-%m-%d').date()
                
                # חישוב ימים מאז תחילת הסבב
                days_diff = (check_date - home_round_date).days
                if days_diff >= 0:
                    # ברירת מחדל: סבב קו (17-4)
                    # כרגע אין שדה cycle_type במסד הנתונים, אז כולם 17-4
                    cycle_type = soldier_data.get('cycle_type', '17-4')
                    
                    if cycle_type == '11-3':
                        # בדיקה: יציאות הביתה (11-3)
                        cycle_day_14 = days_diff % 14
                        if cycle_day_14 >= 11:
                            return False # בבית - לא זמין
                    else:
                        # בדיקה: סבב קו (17-4) - 4 ימים ראשונים הם סבב קו
                        cycle_day_21 = days_diff % 21
                        if cycle_day_21 < 4:
                            return False # בסבב קו - לא זמין

            return True

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
                        'is_base_task': template.is_base_task,
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

                # שימוש ב-SmartScheduler (ML) בלבד - מערכת חכמה שלומדת מפידבק!
                all_available = available_commanders + available_drivers + available_soldiers
                result = smart_scheduler.assign_task(assign_data, all_available, schedules, mahlaka_workload)

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

                    # הוספת חיילים (עם מניעת כפילויות)
                    all_soldier_ids = []
                    seen_soldier_ids = set()
                    for role_key in ['commanders', 'drivers', 'soldiers']:
                        if role_key in result:
                            role_name = role_key[:-1]  # הסרת 's'
                            for soldier_id in result[role_key]:
                                if soldier_id in seen_soldier_ids:
                                    continue  # מניעת כפילות - חייל כבר משובץ במשימה זו
                                seen_soldier_ids.add(soldier_id)
                                assign_soldier = AssignmentSoldier(
                                    assignment_id=assignment.id,
                                    soldier_id=soldier_id,
                                    role_in_assignment=role_name
                                )
                                session.add(assign_soldier)
                                all_soldier_ids.append(soldier_id)

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

                    # Sync to Ditto
                    try:
                        assignment_data = {
                            "shavzak_id": assignment.shavzak_id,
                            "name": assignment.name,
                            "assignment_type": assignment.assignment_type,
                            "day": assignment.day,
                            "start_hour": assignment.start_hour,
                            "length_in_hours": assignment.length_in_hours,
                            "assigned_mahlaka_id": assignment.assigned_mahlaka_id,
                            "soldier_ids": all_soldier_ids,
                            "type": "assignment",
                            "_id": str(assignment.id)
                        }
                        ditto.upsert("assignments", assignment_data)
                    except Exception as e:
                        print(f"⚠️ Failed to sync assignment to Ditto: {e}")

            except Exception as e:
                error_msg = str(e)
                failed_assignments.append((assign_data, error_msg))
                print(f"🔴 שגיאה ביצירת שיבוץ: {error_msg}")
                traceback.print_exc()

        session.commit()

        # חישוב סטטיסטיקות
        total_assignments = session.query(Assignment).filter_by(shavzak_id=shavzak_id).count()

        # עדכון וושמירת מודל ML
        smart_scheduler.stats['total_assignments'] += total_assignments
        smart_scheduler.stats['successful_assignments'] += total_assignments
        smart_scheduler.save_model(ML_MODEL_PATH)
        print(f"✅ מודל ML נשמר עם {total_assignments} משימות חדשות")

        return jsonify({
            'message': 'שיבוץ בוצע בהצלחה עם ML!',
            'failed_assignments': [{'name': a[0]['name'], 'error': a[1]} for a in failed_assignments],
            'stats': {
                'total_assignments': total_assignments,
                'failed_count': len(failed_assignments),
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


@schedule_bp.route('/api/shavzakim/<int:shavzak_id>', methods=['GET'])
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


@schedule_bp.route('/api/plugot/<int:pluga_id>/shavzakim', methods=['GET'])
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


@schedule_bp.route('/api/shavzakim/<int:shavzak_id>', methods=['PUT'])
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


@schedule_bp.route('/api/shavzakim/<int:shavzak_id>', methods=['DELETE'])
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


# ============================================================================
# ASSIGNMENTS - ניהול משימות
# ============================================================================

@schedule_bp.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
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
        assignment_id_str = str(assignment.id)
        session.delete(assignment)
        session.commit()

        # Sync to Ditto
        try:
            ditto.delete("assignments", assignment_id_str)
        except Exception as e:
            print(f"⚠️ Failed to sync assignment deletion to Ditto: {e}")

        return jsonify({'message': 'משימה נמחקה בהצלחה'}), 200
    except Exception as e:
        print(f"🔴 שגיאה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@schedule_bp.route('/api/assignments/<int:assignment_id>/duplicate', methods=['POST'])
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


@schedule_bp.route('/api/shavzakim/<int:shavzak_id>/assignments', methods=['POST'])
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


@schedule_bp.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
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
        soldier_ids = []
        soldier_assignments = session.query(AssignmentSoldier).filter_by(
            assignment_id=assignment.id
        ).all()

        for sa in soldier_assignments:
            soldier_ids.append(sa.soldier_id)
            soldier = session.query(Soldier).filter_by(id=sa.soldier_id).first()
            if soldier:
                soldiers.append({
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'role_in_assignment': sa.role_in_assignment,
                    'mahlaka_id': soldier.mahlaka_id
                })

        # Sync to Ditto
        try:
            assignment_data = {
                "shavzak_id": assignment.shavzak_id,
                "name": assignment.name,
                "assignment_type": assignment.assignment_type,
                "day": assignment.day,
                "start_hour": assignment.start_hour,
                "length_in_hours": assignment.length_in_hours,
                "assigned_mahlaka_id": assignment.assigned_mahlaka_id,
                "soldier_ids": soldier_ids,
                "type": "assignment",
                "_id": str(assignment.id)
            }
            ditto.upsert("assignments", assignment_data)
        except Exception as e:
            print(f"⚠️ Failed to sync assignment update to Ditto: {e}")

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


@schedule_bp.route('/api/assignments/<int:assignment_id>/time', methods=['PATCH'])
@token_required
def update_assignment_time(assignment_id, current_user):
    """עדכון שעת התחלה ו/או שם של משימה (לדרג-אנד-דרופ)"""
    try:
        session = get_db()

        assignment = session.query(Assignment).filter_by(id=assignment_id).first()
        if not assignment:
            return jsonify({'error': 'משימה לא נמצאה'}), 404

        shavzak = session.query(Shavzak).filter_by(id=assignment.shavzak_id).first()
        if not can_edit_pluga(current_user, shavzak.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        data = request.json
        new_start_hour = data.get('start_hour')
        new_name = data.get('name')

        # לפחות אחד מהשדות חייב להיות
        if new_start_hour is None and new_name is None:
            return jsonify({'error': 'חסר לפחות אחד מהפרמטרים: start_hour או name'}), 400

        # אם יש start_hour, בדוק תקינות
        if new_start_hour is not None:
            if not (0 <= new_start_hour < 24):
                return jsonify({'error': 'שעת התחלה לא חוקית (0-23)'}), 400
            assignment.start_hour = new_start_hour

        # אם יש name, בדוק תקינות ועדכן
        if new_name is not None:
            if not new_name.strip():
                return jsonify({'error': 'שם משימה לא יכול להיות ריק'}), 400
            assignment.name = new_name.strip()

        session.commit()

        # Sync to Ditto
        try:
            soldier_ids = [sa.soldier_id for sa in session.query(AssignmentSoldier).filter_by(assignment_id=assignment.id).all()]
            assignment_data = {
                "shavzak_id": assignment.shavzak_id,
                "name": assignment.name,
                "assignment_type": assignment.assignment_type,
                "day": assignment.day,
                "start_hour": assignment.start_hour,
                "length_in_hours": assignment.length_in_hours,
                "assigned_mahlaka_id": assignment.assigned_mahlaka_id,
                "soldier_ids": soldier_ids,
                "type": "assignment",
                "_id": str(assignment.id)
            }
            ditto.upsert("assignments", assignment_data)
        except Exception as e:
            print(f"⚠️ Failed to sync assignment time update to Ditto: {e}")

        return jsonify({
            'message': 'המשימה עודכנה בהצלחה',
            'assignment': {
                'id': assignment.id,
                'start_hour': assignment.start_hour,
                'name': assignment.name
            }
        }), 200
    except Exception as e:
        print(f"🔴 שגיאה בעדכון משימה: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@schedule_bp.route('/api/assignments/<int:assignment_id>/soldiers', methods=['PUT'])
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
        soldier_ids = []
        soldier_assignments = session.query(AssignmentSoldier).filter_by(
            assignment_id=assignment_id
        ).all()

        for sa in soldier_assignments:
            soldier_ids.append(sa.soldier_id)
            soldier = session.query(Soldier).filter_by(id=sa.soldier_id).first()
            if soldier:
                soldiers.append({
                    'id': soldier.id,
                    'name': soldier.name,
                    'role': soldier.role,
                    'role_in_assignment': sa.role_in_assignment,
                    'mahlaka_id': soldier.mahlaka_id
                })

        # Sync to Ditto
        try:
            assignment_data = {
                "shavzak_id": assignment.shavzak_id,
                "name": assignment.name,
                "assignment_type": assignment.assignment_type,
                "day": assignment.day,
                "start_hour": assignment.start_hour,
                "length_in_hours": assignment.length_in_hours,
                "assigned_mahlaka_id": assignment.assigned_mahlaka_id,
                "soldier_ids": soldier_ids,
                "type": "assignment",
                "_id": str(assignment.id)
            }
            ditto.upsert("assignments", assignment_data)
        except Exception as e:
            print(f"⚠️ Failed to sync assignment soldiers update to Ditto: {e}")

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
# LIVE/CONTINUOUS SCHEDULING - שיבוץ חי מתמשך
# ============================================================================

@schedule_bp.route('/api/plugot/<int:pluga_id>/live-schedule', methods=['GET'])
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
                    # הרץ את אלגוריתם השיבוץ ML באופן סינכרוני (פעם אחת בלבד)
                    # זה יכול לקחת כמה שניות, אבל זה קורה רק בפעם הראשונה

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
                                'status_type': status.status_type if status else 'בבסיס',
                                'mahlaka_id': mahlaka.id,
                                'mahlaka_is_special': mahlaka.is_special
                            }

                            # כל חייל מופיע רק ברשימה אחת
                            if soldier.role in ['ממ', 'מכ', 'סמל']:
                                commanders.append(soldier_data)
                            elif 'נהג' in cert_list:
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
                        """בודק אם חייל זמין ביום מסוים, תוך התחשבות בנוכחות, התש"ב 2 וסטטוס"""
                        # בדוק סטטוס החייל - חיילים שלא בבסיס לא זמינים
                        status_type = soldier_data.get('status_type', 'בבסיס')

                        # רשימת סטטוסים שמונעים שיבוץ
                        unavailable_statuses = ['ריתוק', 'לא בבסיס', 'חופשה', 'מילואים', 'גימלים', 'בסבב קו', 'בקשת יציאה']

                        if status_type in unavailable_statuses:
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

                        # בדוק סבב יציאה (אם מוגדר)
                        # אם תאריך סבב היציאה מוגדר, נחשב אם החייל בבית או בסבב קו
                        home_round_date = soldier_data.get('home_round_date')
                        if home_round_date:
                            if isinstance(home_round_date, str):
                                home_round_date = datetime.strptime(home_round_date, '%Y-%m-%d').date()
                            
                            # חישוב ימים מאז תחילת הסבב
                            days_diff = (check_date - home_round_date).days
                            if days_diff >= 0:
                                # ברירת מחדל: סבב קו (17-4)
                                # כרגע אין שדה cycle_type במסד הנתונים, אז כולם 17-4
                                cycle_type = soldier_data.get('cycle_type', '17-4')
                                
                                if cycle_type == '11-3':
                                    # בדיקה: יציאות הביתה (11-3)
                                    cycle_day_14 = days_diff % 14
                                    if cycle_day_14 >= 11:
                                        return False # בבית - לא זמין
                                else:
                                    # בדיקה: סבב קו (17-4) - 4 ימים ראשונים הם סבב קו
                                    cycle_day_21 = days_diff % 21
                                    if cycle_day_21 < 4:
                                        return False # בסבב קו - לא זמין

                        return True

                    # יצירת משימות עם ML - מהיום הנוכחי ועד 7 ימים קדימה
                    all_assignments = []
                    today = datetime.now().date()
                    # חשב את היום הנוכחי יחסית ל-start_date
                    today_offset = (today - master_shavzak.start_date).days
                    # יצירת משימות מהיום הנוכחי ועד 7 ימים קדימה (או עד הסוף)
                    start_day = max(0, today_offset)  # לא ליצור משימות לעבר
                    end_day = min(master_shavzak.days_count, start_day + 7)

                    print(f"🔄 יוצר משימות מיום {start_day} עד יום {end_day} (היום הנוכחי: {today_offset})")

                    for day in range(start_day, end_day):
                        current_date = master_shavzak.start_date + timedelta(days=day)

                        for template in templates:
                            # טיפול במשימות רב-יומיות
                            if template.duration_days > 0:
                                # בדוק אם המשימה צריכה להתחיל ביום הזה
                                # חישוב: (יום נוכחי - אופסט) % אינטרוול == 0
                                # וגם: יום נוכחי >= אופסט
                                if day >= template.start_day_offset and \
                                   (day - template.start_day_offset) % template.recurrence_interval == 0:
                                    
                                    # יצירת משימה אחת ארוכה
                                    assign_data = {
                                        'name': template.name,
                                        'type': template.assignment_type,
                                        'day': day,
                                        'start_hour': template.start_hour or 8, # ברירת מחדל 8 בבוקר
                                        'length_in_hours': template.duration_days * 24, # המרה לשעות
                                        'commanders_needed': template.commanders_needed,
                                        'drivers_needed': template.drivers_needed,
                                        'soldiers_needed': template.soldiers_needed,
                                        'same_mahlaka_required': template.same_mahlaka_required,
                                        'requires_certification': template.requires_certification,
                                        'requires_senior_commander': template.requires_senior_commander,
                                        'reuse_soldiers_for_standby': template.reuse_soldiers_for_standby,
                                        'requires_special_mahlaka': template.requires_special_mahlaka,
                                        'date': current_date,
                                        'is_base_task': template.is_base_task
                                    }
                                    all_assignments.append(assign_data)
                                continue

                            # טיפול במשימות רגילות (לפי שעות)
                            # אם המשימה ניתנת לפיצול (can_split), ניצור שתי משימות נפרדות
                            if template.can_split:
                                # נניח פיצול לשני חלקים שווים עם רווח ביניהם
                                # למשל: פתיחה בבוקר, סגירה בערב
                                # אם לא מוגדרת שעה, נניח 06:00 ו-18:00
                                # אם מוגדרת שעה, נניח שזו שעת ההתחלה של החלק הראשון
                                
                                # שימוש בחלוקה שלמה כדי למנוע שברים (ה-DB דורש Integer)
                                part_length_1 = template.length_in_hours // 2
                                part_length_2 = template.length_in_hours - part_length_1
                                
                                # חלק 1 - פתיחה
                                start_hour_1 = template.start_hour if template.start_hour is not None else 6
                                
                                assign_data_1 = {
                                    'name': f"{template.name} (פתיחה)",
                                    'type': template.assignment_type,
                                    'day': day,
                                    'start_hour': start_hour_1,
                                    'length_in_hours': part_length_1,
                                    'commanders_needed': template.commanders_needed,
                                    'drivers_needed': template.drivers_needed,
                                    'soldiers_needed': template.soldiers_needed,
                                    'same_mahlaka_required': template.same_mahlaka_required,
                                    'requires_certification': template.requires_certification,
                                    'requires_senior_commander': template.requires_senior_commander,
                                    'reuse_soldiers_for_standby': template.reuse_soldiers_for_standby,
                                    'requires_special_mahlaka': template.requires_special_mahlaka,
                                    'date': current_date,
                                    'is_base_task': template.is_base_task
                                }
                                all_assignments.append(assign_data_1)
                                
                                # חלק 2 - סגירה (אחרי 12 שעות או בסוף היום)
                                # אם החלק הראשון ב-6, השני ב-18
                                start_hour_2 = start_hour_1 + 12
                                if start_hour_2 + part_length_2 > 24:
                                    start_hour_2 = 24 - part_length_2 # דוחף לסוף היום אם חורג
                                
                                assign_data_2 = {
                                    'name': f"{template.name} (סגירה)",
                                    'type': template.assignment_type,
                                    'day': day,
                                    'start_hour': start_hour_2,
                                    'length_in_hours': part_length_2,
                                    'commanders_needed': template.commanders_needed,
                                    'drivers_needed': template.drivers_needed,
                                    'soldiers_needed': template.soldiers_needed,
                                    'same_mahlaka_required': template.same_mahlaka_required,
                                    'requires_certification': template.requires_certification,
                                    'requires_senior_commander': template.requires_senior_commander,
                                    'reuse_soldiers_for_standby': template.reuse_soldiers_for_standby,
                                    'requires_special_mahlaka': template.requires_special_mahlaka,
                                    'date': current_date,
                                    'is_base_task': template.is_base_task
                                }
                                all_assignments.append(assign_data_2)
                                
                                continue

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
                                    'requires_special_mahlaka': template.requires_special_mahlaka,
                                    'date': current_date,
                                    'is_base_task': template.is_base_task
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
                            # בדוק אם זו משימת בסיס (נצטרך לשלוף את התבנית או להניח לפי שם/סוג)
                            # לצורך פשטות, נניח כרגע False אלא אם כן נשמור את זה ב-Assignment בעתיד
                            # אבל רגע, הוספנו is_base_task לתבנית, לא למשימה עצמה ב-DB.
                            # אז נצטרך לבדוק מול התבנית.
                            
                            # שליפת התבנית לפי שם (קצת יקר, אבל נחוץ)
                            # או שנשמור is_base_task ב-Assignment בעתיד.
                            # בינתיים ננסה לנחש או נשאיר False
                            is_base = False 
                            # TODO: לשפר את זה ע"י שמירת is_base_task בטבלת assignments
                            
                            schedules[soldier_id].append((
                                existing_assignment.day,
                                existing_assignment.start_hour,
                                existing_assignment.start_hour + existing_assignment.length_in_hours,
                                existing_assignment.name,
                                existing_assignment.assignment_type,
                                is_base
                            ))

                    # מחק משימות קיימות מהימים שאנחנו עומדים ליצור (כדי למנוע כפילויות)
                    days_to_create = set(range(start_day, end_day))
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

                            # שימוש ב-ML בלבד
                            all_available = available_commanders + available_drivers + available_soldiers
                            result = smart_scheduler.assign_task(assign_data, all_available, schedules, mahlaka_workload)

                            if result:
                                # שמירת משימה ב-DB
                                assignment = Assignment(
                                    shavzak_id=master_shavzak.id,
                                    name=assign_data['name'],
                                    assignment_type=assign_data['type'],
                                    day=assign_data['day'],
                                    start_hour=assign_data['start_hour'],
                                    length_in_hours=assign_data['length_in_hours'],
                                    requires_special_mahlaka=assign_data.get('requires_special_mahlaka', False),
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
                                            
                                            # הוסף דגל is_base_task ל-schedule
                                            is_base = assign_data.get('is_base_task', False)
                                            
                                            schedules[soldier_id].append((
                                                assign_data['day'],
                                                assign_data['start_hour'],
                                                assign_data['start_hour'] + assign_data['length_in_hours'],
                                                assign_data['name'],
                                                assign_data['type'],
                                                is_base
                                            ))

                        except Exception as e:
                            error_msg = str(e)
                            failed_assignments.append((assign_data, error_msg))
                            print(f"🔴 שגיאה ביצירת שיבוץ: {error_msg}")
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
        # 🐛 Debug logging
        total_assignments_in_shavzak = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id
        ).count()
        print(f"🔍 DEBUG live-schedule: shavzak_id={master_shavzak.id}, סה\"כ משימות={total_assignments_in_shavzak}")
        print(f"🔍 DEBUG live-schedule: requested_date={requested_date}, master_start_date={master_shavzak.start_date}, day_diff={day_diff}")

        # בדוק לאיזה days יש משימות
        all_days_with_assignments = session.query(Assignment.day).filter(
            Assignment.shavzak_id == master_shavzak.id
        ).distinct().all()
        print(f"🔍 DEBUG live-schedule: ימים עם משימות: {[d[0] for d in all_days_with_assignments]}")

        # חישוב טווח שעות אבסולוטי ליום המבוקש
        day_start_abs = day_diff * 24
        day_end_abs = (day_diff + 1) * 24

        # מצא משימות שחופפות ליום זה (כולל משימות רב-יומיות)
        existing_assignments = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            (Assignment.day * 24 + Assignment.start_hour) < day_end_abs,
            (Assignment.day * 24 + Assignment.start_hour + Assignment.length_in_hours) > day_start_abs
        ).all()

        print(f"🔍 DEBUG live-schedule: מצאתי {len(existing_assignments)} משימות חופפות ליום {day_diff}")

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

                    # בדיקה אם המשימה מוגדרת כניתנת לוויתור
                    if template.is_skippable:
                        severity = "warning" # לא קריטי, כי זה מתוכנן
                        suggest_deletion = True
                        suggestion = "משימה זו מוגדרת כניתנת לוויתור. עקב חוסר בכוח אדם, מומלץ לבטל אותה."
                    elif total_assigned == 0:
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

            # חישוב שעות תצוגה ליום הנוכחי (עבור משימות רב-יומיות)
            assign_start_abs = assignment.day * 24 + assignment.start_hour
            assign_end_abs = assign_start_abs + assignment.length_in_hours
            
            # חיתוך לטווח היום הנוכחי
            effective_start_abs = max(assign_start_abs, day_start_abs)
            effective_end_abs = min(assign_end_abs, day_end_abs)
            
            # המרה לשעות יחסיות ליום (0-24)
            display_start_hour = effective_start_abs - day_start_abs
            display_length = effective_end_abs - effective_start_abs

            assignments_data.append({
                'id': assignment.id,
                'name': assignment.name,
                'type': assignment.assignment_type,
                'day': assignment.day,
                'start_hour': assignment.start_hour,
                'length_in_hours': assignment.length_in_hours,
                'display_start_hour': display_start_hour,
                'display_length_in_hours': display_length,
                'assigned_mahlaka_id': assignment.assigned_mahlaka_id,
                'soldiers': soldiers_list,
                'is_base_task': template.is_base_task if template else False
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


@schedule_bp.route('/api/plugot/<int:pluga_id>/live-schedule/regenerate', methods=['POST'])
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
# SCHEDULING CONSTRAINTS - אילוצי שיבוץ
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


@schedule_bp.route('/api/plugot/<int:pluga_id>/constraints', methods=['GET'])
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


@schedule_bp.route('/api/plugot/<int:pluga_id>/constraints', methods=['POST'])
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


@schedule_bp.route('/api/constraints/<int:constraint_id>', methods=['DELETE'])
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


@schedule_bp.route('/api/plugot/<int:pluga_id>/recent-assignments', methods=['GET'])
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


@schedule_bp.route('/api/plugot/<int:pluga_id>/live-schedule/days/<string:date_str>', methods=['DELETE'])
@token_required
def delete_day_schedule(pluga_id, date_str, current_user):
    """
    מחיקת כל המשימות ליום ספציפי בשיבוץ האוטומטי
    """
    session = get_db()
    try:
        # בדיקת הרשאות - רק מפקדים יכולים לבצע פעולה זו
        if not can_edit_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה לעדכן שיבוץ'}), 403

        # המרת תאריך
        try:
            requested_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'פורמט תאריך לא תקין (YYYY-MM-DD)'}), 400

        # מצא את השיבוץ האוטומטי
        master_shavzak = session.query(Shavzak).filter(
            Shavzak.pluga_id == pluga_id,
            Shavzak.name == 'שיבוץ אוטומטי'
        ).first()

        if not master_shavzak:
            return jsonify({'error': 'לא נמצא שיבוץ אוטומטי'}), 404

        # חישוב יום בשיבוץ
        day_diff = (requested_date - master_shavzak.start_date).days

        if day_diff < 0:
            return jsonify({'error': 'התאריך המבוקש קודם לתאריך התחלת השיבוץ'}), 400

        # מצא את כל המשימות ליום זה
        assignments = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day == day_diff
        ).all()

        if not assignments:
            return jsonify({'message': 'לא נמצאו משימות למחיקה ביום זה'}), 200

        count = 0
        for assignment in assignments:
            # מחק את כל השיוכים של המשימה
            session.query(AssignmentSoldier).filter(
                AssignmentSoldier.assignment_id == assignment.id
            ).delete()
            # מחק את המשימה עצמה
            session.delete(assignment)
            count += 1

        session.commit()
        print(f"✅ נמחקו {count} משימות מהשיבוץ האוטומטי ליום {date_str}")

        return jsonify({
            'success': True,
            'message': f'נמחקו {count} משימות מהשיבוץ ליום {date_str}',
            'deleted_count': count
        }), 200

    except Exception as e:
        session.rollback()
        print(f"Error in delete_day_schedule: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'שגיאה במחיקת השיבוץ ליום: {str(e)}'}), 500
    finally:
        session.close()


@schedule_bp.route('/api/plugot/<int:pluga_id>/live-schedule/days/<string:date_str>/clear-soldiers', methods=['POST'])
@token_required
def clear_day_soldiers(pluga_id, date_str, current_user):
    """
    ניקוי שיבוץ ליום ספציפי - מחיקת החיילים המשובצים אך השארת המשימות (העמודות)
    """
    session = get_db()
    try:
        # בדיקת הרשאות - רק מפקדים יכולים לבצע פעולה זו
        if not can_edit_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה לעדכן שיבוץ'}), 403

        # המרת תאריך
        try:
            requested_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'פורמט תאריך לא תקין (YYYY-MM-DD)'}), 400

        # מצא את השיבוץ האוטומטי
        master_shavzak = session.query(Shavzak).filter(
            Shavzak.pluga_id == pluga_id,
            Shavzak.name == 'שיבוץ אוטומטי'
        ).first()

        if not master_shavzak:
            return jsonify({'error': 'לא נמצא שיבוץ אוטומטי'}), 404

        # חישוב יום בשיבוץ
        day_diff = (requested_date - master_shavzak.start_date).days

        if day_diff < 0:
            return jsonify({'error': 'התאריך המבוקש קודם לתאריך התחלת השיבוץ'}), 400

        # מצא את כל המשימות ליום זה
        assignments = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day == day_diff
        ).all()

        if not assignments:
            return jsonify({'message': 'לא נמצאו משימות לניקוי ביום זה'}), 200

        count = 0
        for assignment in assignments:
            # מחק את כל השיוכים של המשימה בלבד
            deleted = session.query(AssignmentSoldier).filter(
                AssignmentSoldier.assignment_id == assignment.id
            ).delete()
            count += deleted

        session.commit()
        print(f"✅ נמחקו {count} שיבוצי חיילים מהשיבוץ האוטומטי ליום {date_str}")

        return jsonify({
            'success': True,
            'message': f'נמחקו {count} שיבוצי חיילים. המשימות נשמרו.',
            'deleted_count': count
        }), 200

    except Exception as e:
        session.rollback()
        print(f"Error in clear_day_soldiers: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'שגיאה בניקוי השיבוץ ליום: {str(e)}'}), 500
    finally:
        session.close()


@schedule_bp.route('/api/plugot/<int:pluga_id>/export/csv', methods=['GET'])
@token_required
def export_shavzak_csv(pluga_id, current_user):
    """ייצוא שיבוץ ל-CSV (עבור Excel/Sheets)"""
    session = get_db()
    try:
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        start_date_str = request.args.get('start_date')
        days_count = int(request.args.get('days_count', 1))

        if not start_date_str:
            return jsonify({'error': 'חובה לציין תאריך התחלה'}), 400

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=days_count)

        # מצא את השיבוץ האוטומטי
        master_shavzak = session.query(Shavzak).filter(
            Shavzak.pluga_id == pluga_id,
            Shavzak.name == 'שיבוץ אוטומטי'
        ).first()

        if not master_shavzak:
            return jsonify({'error': 'לא נמצא שיבוץ אוטומטי'}), 404

        # חישוב טווח ימים בשיבוץ
        start_day_idx = (start_date - master_shavzak.start_date).days
        end_day_idx = start_day_idx + days_count

        # שליפת משימות
        assignments = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day >= start_day_idx,
            Assignment.day < end_day_idx
        ).order_by(Assignment.day, Assignment.start_hour).all()

        # הכנת CSV
        output = io.StringIO()
        writer = csv.writer(output, encoding='utf-8-sig') # utf-8-sig for Excel Hebrew support

        # כותרות
        writer.writerow(['תאריך', 'יום', 'שעה', 'משימה', 'סוג', 'חיילים משובצים', 'הערות'])

        days_map = {0: 'ראשון', 1: 'שני', 2: 'שלישי', 3: 'רביעי', 4: 'חמישי', 5: 'שישי', 6: 'שבת'}

        for assignment in assignments:
            assign_date = master_shavzak.start_date + timedelta(days=assignment.day)
            day_name = days_map[assign_date.weekday()]
            
            # שליפת חיילים
            soldiers_names = []
            for sa in assignment.soldiers_assigned:
                soldier = session.query(Soldier).get(sa.soldier_id)
                if soldier:
                    role_suffix = f" ({sa.role_in_assignment})" if sa.role_in_assignment and sa.role_in_assignment != 'חייל' else ""
                    soldiers_names.append(f"{soldier.name}{role_suffix}")
            
            soldiers_str = ", ".join(soldiers_names)
            
            writer.writerow([
                assign_date.strftime('%d/%m/%Y'),
                day_name,
                f"{assignment.start_hour:02d}:00",
                assignment.name,
                assignment.assignment_type,
                soldiers_str,
                "" # הערות placeholder
            ])

        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'shavzak_export_{start_date_str}.csv'
        )

    except Exception as e:
        print(f"Error exporting CSV: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
