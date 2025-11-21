"""
ML Routes Blueprint
כל ה-routes הקשורים למערכת הלמידה המכונית (ML)
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import traceback
import json
import os
import base64
from io import BytesIO

from models import (
    get_session, Shavzak, Assignment, AssignmentSoldier, Pluga, Mahlaka,
    Soldier, UnavailableDate, Certification, AssignmentTemplate,
    SoldierStatus, SchedulingConstraint, ConstraintFeedback,
    FeedbackHistory, ScheduleIteration
)
from auth import (
    token_required,
    can_view_pluga, can_edit_pluga
)
from .utils import get_db
from smart_scheduler import SmartScheduler

ml_bp = Blueprint('ml', __name__)

# אתחול המודל ML
ML_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_model.pkl')
smart_scheduler = SmartScheduler()

# נסה לטעון מודל קיים
if os.path.exists(ML_MODEL_PATH):
    smart_scheduler.load_model(ML_MODEL_PATH)
    print("✅ Smart Scheduler (ml_bp): מודל נטען מ-ml_model.pkl")
else:
    print("⚠️ Smart Scheduler (ml_bp): אין מודל קיים - יש לאמן תחילה")


# ============================================================================
# ML TRAINING & SCHEDULING
# ============================================================================

@ml_bp.route('/api/ml/train', methods=['POST'])
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


@ml_bp.route('/api/ml/smart-schedule', methods=['POST'])
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
    session = get_db()

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
                if 'נהג' in cert_list:
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
            status_type = soldier_data.get('status_type', 'בבסיס')

            # חיילים בריתוק או בסבב קו לא זמינים
            if status_type in ['ריתוק', 'בסבב קו']:
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
                start_date=start_date,
                days_count=days_count,
                min_rest_hours=8,
                emergency_mode=False,
                created_at=datetime.now()
            )
            session.add(master_shavzak)
            session.flush()
        else:
            # עדכן את טווח התאריכים אם נדרש
            if start_date < master_shavzak.start_date:
                master_shavzak.start_date = start_date

            end_date_needed = start_date + timedelta(days=days_count)
            current_end_date = master_shavzak.start_date + timedelta(days=master_shavzak.days_count)
            if end_date_needed > current_end_date:
                master_shavzak.days_count = (end_date_needed - master_shavzak.start_date).days

            session.flush()

        # מחק משימות קיימות בטווח התאריכים הנוכחי
        day_start = (start_date - master_shavzak.start_date).days
        days_to_delete = list(range(day_start, day_start + days_count))

        # מחק גם את החיילים המשובצים למשימות האלה
        assignments_to_delete = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day.in_(days_to_delete)
        ).all()

        for assignment in assignments_to_delete:
            session.query(AssignmentSoldier).filter(
                AssignmentSoldier.assignment_id == assignment.id
            ).delete()

        session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day.in_(days_to_delete)
        ).delete(synchronize_session=False)
        session.commit()

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

                # שמור את המשימה למסד הנתונים
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

                # הוסף חיילים למשימה
                for role_key in ['commanders', 'drivers', 'soldiers']:
                    if role_key in result:
                        role_name = 'מפקד' if role_key == 'commanders' else ('נהג' if role_key == 'drivers' else 'חייל')
                        for soldier_id in result[role_key]:
                            assign_soldier = AssignmentSoldier(
                                assignment_id=assignment.id,
                                soldier_id=soldier_id,
                                role_in_assignment=role_name
                            )
                            session.add(assign_soldier)

            else:
                # משימה לא השתבצה - שמור לדיווח
                failed_assignments.append(assign_data)
                print(f"❌ לא הצלחתי לשבץ: {assign_data['name']} ({assign_data['type']}) יום {assign_data['day']} שעה {assign_data['start_hour']}")

        # שמור הכל למסד הנתונים
        session.commit()

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


# ============================================================================
# ML FEEDBACK & LEARNING LOOP
# ============================================================================

@ml_bp.route('/api/ml/feedback', methods=['POST'])
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
    session = get_db()

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
        if not rating or rating not in ['approved', 'rejected', 'modified']:
            print(f"❌ rating לא תקין: {rating}, data: {data}")
            return jsonify({'error': 'rating לא תקין', 'received_rating': rating, 'expected': ['approved', 'rejected', 'modified']}), 400

        # טען משימה
        assignment = session.get(Assignment, assignment_id)
        if not assignment:
            return jsonify({'error': 'משימה לא נמצאה'}), 404

        # אם shavzak_id לא סופק, נסה למצוא אותו דרך המשימה
        if shavzak_id is None:
            shavzak_id = assignment.shavzak_id
            print(f"ℹ️ shavzak_id לא סופק, נמצא דרך assignment: {shavzak_id}")

        # וודא ש-shavzak_id קיים
        if shavzak_id is None:
            print(f"❌ לא ניתן למצוא shavzak_id: {data}")
            return jsonify({'error': 'חסר shavzak_id ולא ניתן למצוא אותו דרך המשימה', 'received_data': data}), 400

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


@ml_bp.route('/api/ml/regenerate-schedule', methods=['POST'])
@token_required
def ml_regenerate_schedule(current_user):
    """
    יצירת איטרציה חדשה של שיבוץ אחרי פידבק שלילי

    Body:
    {
        "shavzak_id": 123,
        "assignment_id": 456,  // אופציונלי - במידה ו-shavzak_id לא סופק
        "reason": "פידבק שלילי - יצירת שיבוץ משופר"
    }
    """
    session = get_db()

    try:
        data = request.get_json()
        shavzak_id = data.get('shavzak_id')
        assignment_id = data.get('assignment_id')
        reason = data.get('reason', 'יצירת איטרציה חדשה')

        # אם shavzak_id לא סופק, נסה למצוא אותו דרך המשימה
        if shavzak_id is None and assignment_id is not None:
            assignment = session.get(Assignment, assignment_id)
            if assignment:
                shavzak_id = assignment.shavzak_id
                print(f"ℹ️ regenerate: shavzak_id לא סופק, נמצא דרך assignment: {shavzak_id}")

        # וודא ש-shavzak_id קיים
        if shavzak_id is None:
            print(f"❌ regenerate: חסר shavzak_id: {data}")
            return jsonify({'error': 'חסר shavzak_id או assignment_id', 'received_data': data}), 400

        # טען שיבוץ
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
                if 'נהג' in cert_list:
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
            status_type = soldier_data.get('status_type', 'בבסיס')

            # חיילים בריתוק או בסבב קו לא זמינים
            if status_type in ['ריתוק', 'בסבב קו']:
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
                            role_name = 'מפקד' if role_key == 'commanders' else ('נהג' if role_key == 'drivers' else 'חייל')
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


@ml_bp.route('/api/ml/feedback-history/<int:shavzak_id>', methods=['GET'])
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
    session = get_db()

    try:
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


@ml_bp.route('/api/ml/stats', methods=['GET'])
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


@ml_bp.route('/api/ml/upload-example', methods=['POST'])
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
# CONSTRAINT FEEDBACK
# ============================================================================

@ml_bp.route('/api/ml/constraint-feedback', methods=['POST'])
@token_required
def ml_constraint_feedback(current_user):
    """
    קבלת פידבק על אילוץ שלא התקיים

    Body:
    {
        "constraint_id": 123,
        "violated_assignment_id": 456,
        "good_example_assignment_id": 789,  // אופציונלי
        "notes": "..."  // אופציונלי
    }
    """
    session = get_db()

    try:
        data = request.get_json()
        print(f"📥 Constraint Feedback request: {data}")

        constraint_id = data.get('constraint_id')
        violated_assignment_id = data.get('violated_assignment_id')
        good_example_assignment_id = data.get('good_example_assignment_id')
        notes = data.get('notes', '')

        # וולידציה
        if constraint_id is None:
            return jsonify({'error': 'חסר constraint_id'}), 400
        if violated_assignment_id is None:
            return jsonify({'error': 'חסר violated_assignment_id'}), 400

        # טען אילוץ
        constraint = session.get(SchedulingConstraint, constraint_id)
        if not constraint:
            return jsonify({'error': 'אילוץ לא נמצא'}), 404

        # בדוק הרשאות
        if not can_view_pluga(current_user, constraint.pluga_id):
            return jsonify({'error': 'אין לך הרשאה'}), 403

        # טען משימה שהופרה
        violated_assignment = session.get(Assignment, violated_assignment_id)
        if not violated_assignment:
            return jsonify({'error': 'משימה לא נמצאה'}), 404

        # שמור פידבק
        feedback = ConstraintFeedback(
            constraint_id=constraint_id,
            violated_assignment_id=violated_assignment_id,
            good_example_assignment_id=good_example_assignment_id,
            user_id=current_user.get('user_id'),
            notes=notes
        )
        session.add(feedback)
        session.commit()

        # כאן אפשר להוסיף לוגיקה ללמידת מכונה
        # למשל: smart_scheduler.learn_from_constraint_violation(...)

        print(f"✅ Constraint feedback saved: constraint={constraint_id}, violated={violated_assignment_id}")

        return jsonify({
            'message': 'פידבק נשמר בהצלחה - המערכת תלמד מזה',
            'feedback_id': feedback.id
        }), 200

    except Exception as e:
        print(f"🔴 שגיאה בשמירת פידבק על אילוץ: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# ML EXPLAINABILITY - הסבר בחירות
# ============================================================================

@ml_bp.route('/api/ml/explain-selection', methods=['POST'])
@token_required
def ml_explain_selection(current_user):
    """
    הסבר מפורט למה המודל בחר בחייל מסוים למשימה

    Body:
    {
        "soldier_id": 123,
        "assignment_type": "שמירה",
        "day": 0,
        "start_hour": 8,
        "length_in_hours": 8,
        "shavzak_id": 456,  // אופציונלי - לקבלת קונטקסט
        "pluga_id": 1
    }

    Returns:
    {
        "soldier_name": "...",
        "soldier_role": "...",
        "total_score": 123.4,
        "confidence": 0.85,
        "recommendation": "בחירה מצוינת ✅",
        "breakdown": [
            {
                "factor": "😴 מנוחה",
                "contribution": 48.0,
                "explanation": "24.0 שעות מאז המשימה האחרונה"
            },
            ...
        ]
    }
    """
    session = get_db()

    try:
        data = request.get_json()

        soldier_id = data.get('soldier_id')
        assignment_type = data.get('assignment_type')
        day = data.get('day', 0)
        start_hour = data.get('start_hour', 8)
        length_in_hours = data.get('length_in_hours', 8)
        shavzak_id = data.get('shavzak_id')
        pluga_id = data.get('pluga_id')

        # וולידציה
        if soldier_id is None:
            return jsonify({'error': 'חסר soldier_id'}), 400
        if not assignment_type:
            return jsonify({'error': 'חסר assignment_type'}), 400
        if pluga_id is None:
            return jsonify({'error': 'חסר pluga_id'}), 400

        # בדוק הרשאות
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה לפלוגה זו'}), 403

        # טען חייל
        soldier = session.get(Soldier, soldier_id)
        if not soldier:
            return jsonify({'error': 'חייל לא נמצא'}), 404

        # בנה נתוני משימה
        task = {
            'type': assignment_type,
            'day': day,
            'start_hour': start_hour,
            'length_in_hours': length_in_hours
        }

        # בנה נתוני חייל
        certifications = session.query(Certification).filter_by(soldier_id=soldier_id).all()
        cert_list = [c.certification_name for c in certifications]

        soldier_data = {
            'id': soldier.id,
            'name': soldier.name,
            'role': soldier.role,
            'certifications': cert_list,
            'mahlaka_id': soldier.mahlaka_id
        }

        # טען schedules וכל החיילים (לקונטקסט)
        schedules = {}
        mahlaka_workload = {}
        all_soldiers = []

        if shavzak_id:
            # אם יש shavzak_id, טען את כל המידע הרלוונטי
            shavzak = session.get(Shavzak, shavzak_id)
            if shavzak:
                assignments = session.query(Assignment).filter_by(shavzak_id=shavzak_id).all()

                # בנה schedules מהמשימות הקיימות
                for assignment in assignments:
                    for assigned_soldier in assignment.soldiers_assigned:
                        s_id = assigned_soldier.soldier_id
                        if s_id not in schedules:
                            schedules[s_id] = []
                        schedules[s_id].append((
                            assignment.day,
                            assignment.start_hour,
                            assignment.start_hour + assignment.length_in_hours,
                            assignment.name,
                            assignment.assignment_type
                        ))

                # טען כל החיילים בפלוגה
                all_soldiers_query = session.query(Soldier).join(Mahlaka).filter(
                    Mahlaka.pluga_id == pluga_id
                ).all()

                for s in all_soldiers_query:
                    certs = session.query(Certification).filter_by(soldier_id=s.id).all()
                    all_soldiers.append({
                        'id': s.id,
                        'name': s.name,
                        'role': s.role,
                        'mahlaka_id': s.mahlaka_id,
                        'certifications': [c.certification_name for c in certs]
                    })

                # חשב עומס מחלקות
                mahalkot = session.query(Mahlaka).filter_by(pluga_id=pluga_id).all()
                for mahlaka in mahalkot:
                    mahlaka_workload[mahlaka.id] = 0
                    for assignment in assignments:
                        if assignment.assigned_mahlaka_id == mahlaka.id:
                            mahlaka_workload[mahlaka.id] += assignment.length_in_hours

        # אם אין שיבוץ, השתמש בברירת מחדל
        if not all_soldiers:
            all_soldiers = [soldier_data]

        # קרא להסבר מהמודל
        explanation = smart_scheduler.explain_soldier_selection(
            soldier=soldier_data,
            task=task,
            schedules=schedules,
            mahlaka_workload=mahlaka_workload,
            all_soldiers=all_soldiers
        )

        print(f"✅ Generated explanation for soldier {soldier_id} on task {assignment_type}")

        return jsonify(explanation), 200

    except Exception as e:
        print(f"🔴 שגיאה בהסבר בחירה: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@ml_bp.route('/api/ml/soldier-confidence/<int:soldier_id>', methods=['POST'])
@token_required
def ml_soldier_confidence(current_user, soldier_id):
    """
    קבלת רמת ביטחון המודל בבחירת חייל למשימה

    Body:
    {
        "assignment_type": "שמירה",
        "day": 0,
        "start_hour": 8,
        "length_in_hours": 8,
        "shavzak_id": 456,  // אופציונלי
        "pluga_id": 1
    }

    Returns:
    {
        "soldier_id": 123,
        "soldier_name": "...",
        "score": 123.4,
        "confidence": 0.85,
        "confidence_level": "גבוה" | "בינוני" | "נמוך"
    }
    """
    session = get_db()

    try:
        data = request.get_json()

        assignment_type = data.get('assignment_type')
        day = data.get('day', 0)
        start_hour = data.get('start_hour', 8)
        length_in_hours = data.get('length_in_hours', 8)
        shavzak_id = data.get('shavzak_id')
        pluga_id = data.get('pluga_id')

        # וולידציה
        if not assignment_type:
            return jsonify({'error': 'חסר assignment_type'}), 400
        if pluga_id is None:
            return jsonify({'error': 'חסר pluga_id'}), 400

        # בדוק הרשאות
        if not can_view_pluga(current_user, pluga_id):
            return jsonify({'error': 'אין לך הרשאה לפלוגה זו'}), 403

        # טען חייל
        soldier = session.get(Soldier, soldier_id)
        if not soldier:
            return jsonify({'error': 'חייל לא נמצא'}), 404

        # בנה נתוני משימה
        task = {
            'type': assignment_type,
            'day': day,
            'start_hour': start_hour,
            'length_in_hours': length_in_hours
        }

        # בנה נתוני חייל
        certifications = session.query(Certification).filter_by(soldier_id=soldier_id).all()
        cert_list = [c.certification_name for c in certifications]

        soldier_data = {
            'id': soldier.id,
            'name': soldier.name,
            'role': soldier.role,
            'certifications': cert_list,
            'mahlaka_id': soldier.mahlaka_id
        }

        # טען קונטקסט מינימלי
        schedules = {}
        mahlaka_workload = {}

        if shavzak_id:
            shavzak = session.get(Shavzak, shavzak_id)
            if shavzak:
                assignments = session.query(Assignment).filter_by(shavzak_id=shavzak_id).all()

                # בנה schedules
                for assignment in assignments:
                    for assigned_soldier in assignment.soldiers_assigned:
                        s_id = assigned_soldier.soldier_id
                        if s_id not in schedules:
                            schedules[s_id] = []
                        schedules[s_id].append((
                            assignment.day,
                            assignment.start_hour,
                            assignment.start_hour + assignment.length_in_hours,
                            assignment.name,
                            assignment.assignment_type
                        ))

        # חשב ציון וביטחון
        score, confidence = smart_scheduler.calculate_soldier_score_with_confidence(
            soldier=soldier_data,
            task=task,
            schedules=schedules,
            mahlaka_workload=mahlaka_workload
        )

        # קבע רמת ביטחון
        if confidence > 0.7:
            confidence_level = "גבוה"
        elif confidence > 0.4:
            confidence_level = "בינוני"
        else:
            confidence_level = "נמוך"

        print(f"✅ Calculated confidence for soldier {soldier_id}: {confidence:.2f} ({confidence_level})")

        return jsonify({
            'soldier_id': soldier_id,
            'soldier_name': soldier.name,
            'score': round(score, 1),
            'confidence': round(confidence, 2),
            'confidence_level': confidence_level
        }), 200

    except Exception as e:
        print(f"🔴 שגיאה בחישוב ביטחון: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
