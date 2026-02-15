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
from sqlalchemy.orm import joinedload, selectinload
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
    try:
        smart_scheduler.load_model(ML_MODEL_PATH)
        print("✅ Smart Scheduler (ml_bp): מודל נטען מ-ml_model.pkl")
    except Exception as e:
        print(f"⚠️ Smart Scheduler (ml_bp): נכשל בטעינת המודל: {e}")
        print("   ממשיך ללא מודל מאומן.")
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

        # הרצת הלוגיקה המופרדת
        result = run_smart_scheduling(
            session=session,
            pluga_id=pluga_id,
            start_date=start_date,
            days_count=days_count,
            user_id=current_user.get('user_id')
        )

        if 'error' in result:
            return jsonify({'error': result['error']}), result.get('status', 500)

        return jsonify(result), 200

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


# ============================================================================
# ML STATS
# ============================================================================

@ml_bp.route('/api/ml/stats', methods=['GET'])
@token_required
def ml_stats(current_user):
    """
    קבלת סטטיסטיקות ML - אחוזי אישור, דפוסים שנלמדו, פידבקים
    """
    try:
        stats = smart_scheduler.get_stats()
        return jsonify({'stats': stats}), 200
    except Exception as e:
        print(f"🔴 שגיאה בקבלת סטטיסטיקות ML: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


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

        # בנה מבנה נתונים - 🚀 אופטימיזציה: טעינה מקדימה של כל הנתונים
        # טוען את כל החיילים עם כל הנתונים הקשורים בשאילתה אחת במקום מאות שאילתות!
        all_soldiers_query = session.query(Soldier).options(
            selectinload(Soldier.certifications),
            selectinload(Soldier.unavailable_dates),
            selectinload(Soldier.current_status)
        ).join(Mahlaka).filter(Mahlaka.pluga_id == pluga_id).all()

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
                    if u.date >= start_date and u.date < start_date + timedelta(days=days_count)
                ]

                cert_list = [c.certification_name for c in soldier.certifications]
                status = soldier.current_status

                if status and status.status_type != 'בבסיס':
                    print(f"DEBUG RAW STATUS: {soldier.name} - '{status.status_type}'")

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
                    'status_start_date': status.start_date if status else None,
                    'status_end_date': status.end_date if status else None,
                    'return_date': status.return_date if status else None,
                    'mahlaka_id': mahlaka.id
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

        # פונקציה לבדיקת זמינות
        def is_soldier_available(soldier_data, check_date):
            """בודק אם חייל זמין ביום מסוים, תוך התחשבות בנוכחות, התש"ב 2 וסטטוס"""
            # בדוק סטטוס החייל - חיילים שלא בבסיס לא זמינים
            status_type = soldier_data.get('status_type', 'בבסיס')
            if status_type: status_type = status_type.strip() # נקה רווחים
            
            status_start = soldier_data.get('status_start_date')
            status_end = soldier_data.get('status_end_date')

            unavailable_statuses = ['ריתוק', 'לא בבסיס', 'חופשה', 'מילואים', 'גימלים', 'בסבב קו', 'בקשת יציאה']

            if status_type in unavailable_statuses:
                # אם יש תאריכים, בדוק אם התאריך נופל בטווח
                if status_start and status_end:
                    # המר תאריכים ל-date אם הם מחרוזות
                    if isinstance(status_start, str): status_start = datetime.strptime(status_start, '%Y-%m-%d').date()
                    if isinstance(status_end, str): status_end = datetime.strptime(status_end, '%Y-%m-%d').date()
                    
                    if status_start <= check_date <= status_end:
                        print(f"🚫 {soldier_data['name']} לא זמין ב-{check_date}: סטטוס {status_type} ({status_start} - {status_end})")
                        return False
                    # אחרת - הסטטוס לא תקף לתאריך זה -> זמין (אלא אם יש משהו אחר)
                else:
                    # אין תאריכים - הנח שהסטטוס תקף תמיד
                    print(f"🚫 {soldier_data['name']} לא זמין ב-{check_date}: סטטוס {status_type} (תמיד)")
                    return False
            elif status_type != 'בבסיס':
                # הדפס סטטוסים לא מוכרים לדיבאג
                # print(f"⚠️ סטטוס לא מוכר ל-{soldier_data['name']}: '{status_type}'")
                pass

            # בדוק אם התאריך באי זמינות רגילה
            if check_date in soldier_data.get('unavailable_dates', []):
                print(f"🚫 {soldier_data['name']} לא זמין ב-{check_date}: תאריך אי-זמינות רשום")
                return False

            # בדוק התש"ב 2 - ימים קבועים שהחייל לא זמין
            hatash_2_days = soldier_data.get('hatash_2_days')
            if hatash_2_days:
                day_of_week = check_date.weekday()
                day_of_week = (day_of_week + 1) % 7
                hatash_days_list = hatash_2_days.split(',')
                if str(day_of_week) in hatash_days_list:
                    print(f"🚫 {soldier_data['name']} לא זמין ב-{check_date}: התש\"ב 2 (יום {day_of_week})")
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
                        # תיקון: הנח שהסבב מתחיל בבית (כמו ב-17-4)
                        # 3 ימים בית, 11 ימים בסיס
                        if (days_diff % 14) < 3:
                            print(f"🚫 {soldier_data['name']} לא זמין ב-{check_date}: סבב 11-3 (בבית)")
                            return False
                    else:
                        # בדיקה: סבב קו (17-4) - 4 ימים ראשונים הם סבב קו
                        if (days_diff % 21) < 4:
                            print(f"🚫 {soldier_data['name']} לא זמין ב-{check_date}: סבב 17-4 (בבית)")
                            return False

            return True

        # בנה schedules מכל המשימות *האחרות*
        other_assignments = session.query(Assignment).filter(
            Assignment.shavzak_id == shavzak.id,
            Assignment.id != assignment_id
        ).all()

        schedules = {}
        mahlaka_workload = {m['id']: 0 for m in mahalkot_data}

        for assign in other_assignments:
            # עדכן עומס מחלקתי
            if assign.assigned_mahlaka_id:
                mahlaka_workload[assign.assigned_mahlaka_id] = mahlaka_workload.get(assign.assigned_mahlaka_id, 0) + assign.length_in_hours

            # עדכן לו"ז חיילים
            for soldier in assign.soldiers_assigned:
                if soldier.soldier_id not in schedules:
                    schedules[soldier.soldier_id] = []
                schedules[soldier.soldier_id].append((
                    assign.day,
                    assign.start_hour,
                    assign.start_hour + assign.length_in_hours,
                    assign.name,
                    assign.assignment_type
                ))

        # הכן נתונים לשיבוץ מחדש
        current_date = shavzak.start_date + timedelta(days=assignment.day)
        
        all_commanders = [c for m in mahalkot_data for c in m['commanders']]
        all_drivers = [d for m in mahalkot_data for d in m['drivers']]
        all_soldiers = [s for m in mahalkot_data for s in m['soldiers']]

        # סנן זמינים
        available_commanders = [c for c in all_commanders if is_soldier_available(c, current_date)]
        available_drivers = [d for d in all_drivers if is_soldier_available(d, current_date)]
        available_soldiers = [s for s in all_soldiers if is_soldier_available(s, current_date)]

        all_available = available_commanders + available_drivers + available_soldiers

        # הסר את החיילים הנוכחיים מהרשימה (כדי להכריח החלפה)
        current_soldier_ids = [s.soldier_id for s in assignment.soldiers_assigned]
        all_available = [s for s in all_available if s['id'] not in current_soldier_ids]

        # DEBUG: Print available soldiers
        print(f"🔍 DEBUG: Available for regeneration {assignment.name} ({current_date}): {[s['name'] for s in all_available]}")

        # חישוב דרישות כוח אדם
        commanders_needed = 1 if assignment.assignment_type in ['סיור', 'כוננות א'] else 0
        drivers_needed = 1 if assignment.assignment_type == 'סיור' else 0
        
        # חישוב כמה חיילים רגילים צריך (סך הכל פחות מפקדים ונהגים)
        total_assigned = len(current_soldier_ids)
        soldiers_needed = total_assigned - commanders_needed - drivers_needed
        if soldiers_needed < 0: soldiers_needed = 0

        assign_data = {
            'name': assignment.name,
            'type': assignment.assignment_type,
            'day': assignment.day,
            'start_hour': assignment.start_hour,
            'length_in_hours': assignment.length_in_hours,
            'commanders_needed': commanders_needed,
            'drivers_needed': drivers_needed,
            'soldiers_needed': soldiers_needed,
            'same_mahlaka_required': assignment.assigned_mahlaka_id is not None,
            'date': current_date
        }

        # נסה לשבץ מחדש
        result = smart_scheduler.assign_task(assign_data, all_available, schedules, mahlaka_workload)

        if result:
            # הצליח! עדכן את המשימה
            
            # מחק חיילים ישנים
            session.query(AssignmentSoldier).filter_by(assignment_id=assignment.id).delete()
            
            # עדכן מחלקה
            if result.get('mahlaka_id'):
                assignment.assigned_mahlaka_id = result.get('mahlaka_id')

            # הוסף חיילים חדשים
            new_soldiers_list = []
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
                        
                        # מצא פרטי חייל להחזרה
                        soldier_info = next((s for s in all_available if s['id'] == soldier_id), None)
                        if soldier_info:
                            new_soldiers_list.append({
                                'id': soldier_id,
                                'name': soldier_info['name'],
                                'role': soldier_info['role'],
                                'role_in_assignment': role_name
                            })

            session.commit()
            
            return jsonify({
                'message': 'המשימה שובצה מחדש בהצלחה',
                'assignment': {
                    'id': assignment.id,
                    'soldiers': new_soldiers_list,
                    'assigned_mahlaka_id': assignment.assigned_mahlaka_id
                }
            }), 200
        else:
            return jsonify({'error': 'לא נמצא פתרון חלופי למשימה זו (נסה לשחרר אילוצים או לשבץ ידנית)'}), 400

    except Exception as e:
        print(f"🔴 שגיאה בשיבוץ מחדש: {str(e)}")
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


def run_smart_scheduling(session, pluga_id, start_date, days_count, user_id):
    """
    הרצת לוגיקת השיבוץ החכם (מופרד מה-route כדי לאפשר קריאה מפונקציות אחרות)
    """
    # טען נתונים
    mahalkot = session.query(Mahlaka).filter_by(pluga_id=pluga_id).all()
    templates = session.query(AssignmentTemplate).filter_by(pluga_id=pluga_id).all()

    if not templates:
        return {'error': 'אין תבניות משימות במערכת', 'status': 400}

    # בנה מבנה נתונים - 🚀 אופטימיזציה: טעינה מקדימה של כל הנתונים
    all_soldiers_query = session.query(Soldier).options(
        selectinload(Soldier.certifications),
        selectinload(Soldier.unavailable_dates),
        selectinload(Soldier.current_status)
    ).join(Mahlaka).filter(Mahlaka.pluga_id == pluga_id).all()

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
                if u.date >= start_date and u.date < start_date + timedelta(days=days_count)
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
                'status_start_date': status.start_date if status else None,
                'status_end_date': status.end_date if status else None,
                'return_date': status.return_date if status else None,
                'mahlaka_id': mahlaka.id
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

    # פונקציה לבדיקת זמינות
    def is_soldier_available(soldier_data, check_date):
        """בודק אם חייל זמין ביום מסוים, תוך התחשבות בנוכחות, התש"ב 2 וסטטוס"""
        # בדוק סטטוס החייל - חיילים שלא בבסיס לא זמינים
        status_type = soldier_data.get('status_type', 'בבסיס')
        if status_type: status_type = status_type.strip() # נקה רווחים
        
        status_start = soldier_data.get('status_start_date')
        status_end = soldier_data.get('status_end_date')
        return_date = soldier_data.get('return_date')

        unavailable_statuses = ['ריתוק', 'לא בבסיס', 'חופשה', 'מילואים', 'גימלים', 'בסבב קו', 'בקשת יציאה']

        if status_type in unavailable_statuses:
            # אם יש תאריכים, בדוק אם התאריך נופל בטווח
            if status_start and status_end:
                # המר תאריכים ל-date אם הם מחרוזות
                if isinstance(status_start, str): status_start = datetime.strptime(status_start, '%Y-%m-%d').date()
                if isinstance(status_end, str): status_end = datetime.strptime(status_end, '%Y-%m-%d').date()
                if return_date and isinstance(return_date, str): return_date = datetime.strptime(return_date, '%Y-%m-%d').date()
                
                # אם זה יום החזרה - החייל זמין (חלקית, יטופל ב-SmartScheduler)
                if return_date and check_date == return_date:
                    return True

                if status_start <= check_date <= status_end:
                    # print(f"🚫 {soldier_data['name']} לא זמין ב-{check_date}: סטטוס {status_type} ({status_start} - {status_end})")
                    return False
            else:
                # אין תאריכים - הנח שהסטטוס תקף תמיד
                # print(f"🚫 {soldier_data['name']} לא זמין ב-{check_date}: סטטוס {status_type} (תמיד)")
                return False
        
        # בדוק אם התאריך באי זמינות רגילה
        if check_date in soldier_data.get('unavailable_dates', []):
            # print(f"🚫 {soldier_data['name']} לא זמין ב-{check_date}: תאריך אי-זמינות רשום")
            return False

        # בדוק התש"ב 2 - ימים קבועים שהחייל לא זמין
        hatash_2_days = soldier_data.get('hatash_2_days')
        if hatash_2_days:
            day_of_week = check_date.weekday()
            day_of_week = (day_of_week + 1) % 7
            hatash_days_list = hatash_2_days.split(',')
            if str(day_of_week) in hatash_days_list:
                # print(f"🚫 {soldier_data['name']} לא זמין ב-{check_date}: התש\"ב 2 (יום {day_of_week})")
                return False

        # בדוק סבב יציאה (אם מוגדר)
        home_round_date = soldier_data.get('home_round_date')
        if home_round_date:
            if isinstance(home_round_date, str):
                home_round_date = datetime.strptime(home_round_date, '%Y-%m-%d').date()
            
            days_diff = (check_date - home_round_date).days
            if days_diff >= 0:
                cycle_type = soldier_data.get('cycle_type', '17-4')
                if cycle_type == '11-3':
                    if (days_diff % 14) < 3:
                        return False
                else:
                    if (days_diff % 21) < 4:
                        return False

        return True

    # חפש או צור Shavzak "מאסטר" לפלוגה
    master_shavzak = session.query(Shavzak).filter(
        Shavzak.pluga_id == pluga_id,
        Shavzak.name == 'שיבוץ אוטומטי'
    ).first()

    start_date_changed = False

    if not master_shavzak:
        master_shavzak = Shavzak(
            name='שיבוץ אוטומטי',
            pluga_id=pluga_id,
            created_by=user_id,
            start_date=start_date,
            days_count=days_count,
            min_rest_hours=8,
            emergency_mode=False,
            created_at=datetime.now()
        )
        session.add(master_shavzak)
        session.flush()
    else:
        if start_date < master_shavzak.start_date:
            master_shavzak.start_date = start_date
            start_date_changed = True

        end_date_needed = start_date + timedelta(days=days_count)
        current_end_date = master_shavzak.start_date + timedelta(days=master_shavzak.days_count)
        if end_date_needed > current_end_date:
            master_shavzak.days_count = (end_date_needed - master_shavzak.start_date).days

        session.flush()

    # יצירת משימות
    temp_day_start = 0
    if master_shavzak:
        temp_day_start = (start_date - master_shavzak.start_date).days

    all_assignments = []
    for day in range(days_count):
        current_date = start_date + timedelta(days=day)
        actual_day = temp_day_start + day

        for template in templates:
            for slot in range(template.times_per_day):
                if template.start_hour is not None:
                    start_hour = template.start_hour + (slot * template.length_in_hours)
                else:
                    start_hour = slot * template.length_in_hours

                assign_data = {
                    'name': template.name,
                    'type': template.assignment_type,
                    'day': actual_day,
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

    # מחיקת משימות קיימות
    if start_date_changed:
        days_to_delete = session.query(Assignment.day).filter(
            Assignment.shavzak_id == master_shavzak.id
        ).distinct().all()
        days_to_delete = [d[0] for d in days_to_delete]
    else:
        day_start = (start_date - master_shavzak.start_date).days
        days_to_delete = session.query(Assignment.day).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day >= day_start
        ).distinct().all()
        days_to_delete = [d[0] for d in days_to_delete]

    if days_to_delete:
        assignments_to_delete = session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day.in_(days_to_delete)
        ).all()

        for assignment in assignments_to_delete:
            session.query(AssignmentSoldier).filter(
                AssignmentSoldier.assignment_id == assignment.id
            ).delete()
            session.expunge(assignment)

        session.query(Assignment).filter(
            Assignment.shavzak_id == master_shavzak.id,
            Assignment.day.in_(days_to_delete)
        ).delete(synchronize_session=False)
        session.commit()

    # הרצת ML עם ניסיונות חוזרים (Retry Logic)
    max_attempts = 5
    best_attempt = None
    min_failures = float('inf')

    all_commanders = [c for m in mahalkot_data for c in m['commanders']]
    all_drivers = [d for m in mahalkot_data for d in m['drivers']]
    all_soldiers = [s for m in mahalkot_data for s in m['soldiers']]

    for attempt in range(1, max_attempts + 1):
        print(f"🔄 ניסיון שיבוץ {attempt}/{max_attempts}...")
        
        schedules = {}
        mahlaka_workload = {m['id']: 0 for m in mahalkot_data}
        
        current_created_assignments = []
        current_failed_assignments = []
        validation_failures = 0

        for assign_data in all_assignments:
            current_date = assign_data['date']

            available_commanders = [c for c in all_commanders if is_soldier_available(c, current_date)]
            available_drivers = [d for d in all_drivers if is_soldier_available(d, current_date)]
            available_soldiers = [s for s in all_soldiers if is_soldier_available(s, current_date)]

            all_available = available_commanders + available_drivers + available_soldiers

            # העתק של mahlaka_workload לשימוש בתוך assign_task (כי הוא משנה אותו)
            # אבל אנחנו רוצים שהשינויים יישמרו לאורך הניסיון הנוכחי
            result = smart_scheduler.assign_task(assign_data, all_available, schedules, mahlaka_workload)

            # בדיקת תקינות (Validation)
            is_valid = True
            if not result:
                is_valid = False
            else:
                # בדוק אם עומד בדרישות
                if len(result.get('commanders', [])) < assign_data.get('commanders_needed', 0):
                    is_valid = False
                if len(result.get('drivers', [])) < assign_data.get('drivers_needed', 0):
                    is_valid = False
                if len(result.get('soldiers', [])) < assign_data.get('soldiers_needed', 0):
                    is_valid = False

            if not is_valid:
                validation_failures += 1
                if not result:
                    result = {
                        'commanders': [],
                        'drivers': [],
                        'soldiers': [],
                        'mahlaka_id': None
                    }
                current_failed_assignments.append(assign_data)
            
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

            current_created_assignments.append({
                **assign_data,
                'result': result
            })

        print(f"   ❌ כישלונות בניסיון {attempt}: {validation_failures}")

        # שמור את הניסיון הטוב ביותר
        if validation_failures < min_failures:
            min_failures = validation_failures
            best_attempt = {
                'created_assignments': current_created_assignments,
                'failed_assignments': current_failed_assignments
            }

        # אם השיבוץ מושלם - עצור
        if validation_failures == 0:
            print("✅ נמצא שיבוץ מושלם!")
            break
    
    # השתמש בניסיון הטוב ביותר
    created_assignments = best_attempt['created_assignments']
    failed_assignments = best_attempt['failed_assignments']

    # שמירה לדאטהבייס
    for item in created_assignments:
        result = item['result']
        
        assignment = Assignment(
            shavzak_id=master_shavzak.id,
            name=item['name'],
            assignment_type=item['type'],
            day=item['day'],
            start_hour=item['start_hour'],
            length_in_hours=item['length_in_hours'],
            assigned_mahlaka_id=result.get('mahlaka_id')
        )
        session.add(assignment)
        session.flush()

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

    session.commit()
    
    smart_scheduler.stats['total_assignments'] += len(created_assignments)
    smart_scheduler.stats['successful_assignments'] += len(created_assignments)
    smart_scheduler.save_model(ML_MODEL_PATH)

    return {
        'message': f'נוצרו {len(created_assignments)} משימות בהצלחה',
        'assignments': created_assignments,
        'stats': smart_scheduler.get_stats(),
        'failed_assignments': [
            {'name': f['name'], 'type': f['type'], 'day': f['day'], 'start_hour': f['start_hour']}
            for f in failed_assignments
        ],
        'success_rate': f"{(len(created_assignments) / len(all_assignments) * 100):.1f}%" if all_assignments else "0%"
    }
