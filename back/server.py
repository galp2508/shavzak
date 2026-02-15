"""
Shavzak API Server
מערכת ניהול שיבוצים צבאית
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import traceback
import sys  # Added for exit
import os
import sqlite3

# Load environment variables
load_dotenv()

from models import init_db
from config import Config  # Import Config

app = Flask(__name__)
app.config.from_object(Config)  # Load configuration
CORS(app)

# Rate Limiting Configuration
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["5000 per day", "1000 per hour"],
    storage_uri="memory://",
)

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

        # בדיקה 4.5: הוספת is_special לטבלת mahalkot
        cursor.execute("PRAGMA table_info(mahalkot)")
        mahlaka_columns = [column[1] for column in cursor.fetchall()]

        if 'is_special' not in mahlaka_columns:
            print("⚠️  מזהה עמודה חסרה: is_special בטבלת mahalkot")
            print("🔧 מריץ migration אוטומטי להוספת is_special...")
            conn.close()
            from migrate_add_is_special import migrate_database as migrate_add_special
            if migrate_add_special(DB_PATH):
                print("✅ Migration להוספת is_special הושלם בהצלחה")
            else:
                print("❌ Migration להוספת is_special נכשל")
                return False
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
        else:
            print("✅ is_special כבר קיים")

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

        # בדיקה 6: הוספת reuse_soldiers_for_standby ו-requires_special_mahlaka לטבלת assignment_templates
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
            # Re-fetch columns to be safe for next check
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(assignment_templates)")
            template_columns = [column[1] for column in cursor.fetchall()]

        if 'requires_special_mahlaka' not in template_columns:
            print("⚠️  מזהה עמודה חסרה: requires_special_mahlaka בטבלת assignment_templates")
            print("🔧 מריץ migration אוטומטי להוספת requires_special_mahlaka לתבניות...")
            conn.close()
            from migrate_add_special_to_templates import migrate_database as migrate_special_templates
            if migrate_special_templates(DB_PATH):
                print("✅ Migration להוספת requires_special_mahlaka לתבניות הושלם בהצלחה")
            else:
                print("❌ Migration להוספת requires_special_mahlaka לתבניות נכשל")
                return False
            conn = sqlite3.connect(DB_PATH)
            # cursor = conn.cursor()
        else:
             print("✅ requires_special_mahlaka כבר קיים")

        # בדיקה 7.5: הוספת requires_special_mahlaka לטבלת assignments (המשימות עצמן)
        # זה קריטי כי הקוד מנסה לקרוא את העמודה הזו בכל שליפה של משימות
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(assignments)")
        assignment_columns = [column[1] for column in cursor.fetchall()]

        if 'requires_special_mahlaka' not in assignment_columns:
            print("⚠️  מזהה עמודה חסרה: requires_special_mahlaka בטבלת assignments")
            print("🔧 מריץ migration אוטומטי להוספת requires_special_mahlaka למשימות...")
            conn.close()
            from migrate_add_special_to_assignments import migrate_database as migrate_special_assignments
            if migrate_special_assignments(DB_PATH):
                print("✅ Migration להוספת requires_special_mahlaka למשימות הושלם בהצלחה")
            else:
                print("❌ Migration להוספת requires_special_mahlaka למשימות נכשל")
                return False
            conn = sqlite3.connect(DB_PATH)
            # Re-fetch columns
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(assignment_templates)")
            template_columns = [column[1] for column in cursor.fetchall()]
        else:
             print("✅ requires_special_mahlaka כבר קיים ב-assignments")

        # בדיקה 8: הוספת is_standby_task לטבלת assignment_templates
        # זה מאפשר להגדיר משימות כ"כוננות" שלא דורשות מנוחה אחריהן
        if 'is_standby_task' not in template_columns:
            print("⚠️  מזהה עמודה חסרה: is_standby_task בטבלת assignment_templates")
            print("🔧 מריץ migration אוטומטי להוספת is_standby_task לתבניות...")
            conn.close()
            from migrate_add_standby_to_templates import migrate_database as migrate_standby_templates
            if migrate_standby_templates(DB_PATH):
                print("✅ Migration להוספת is_standby_task לתבניות הושלם בהצלחה")
            else:
                print("❌ Migration להוספת is_standby_task לתבניות נכשל")
                return False
            conn = sqlite3.connect(DB_PATH)
        else:
            print("✅ is_standby_task כבר קיים")

        conn.close()
        return True
    
    except Exception as e:

        print(f"⚠️  שגיאה בבדיקת schema: {e}")
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return False

# הרצת migrations בעת אתחול
if not check_and_run_migrations():
    print("❌ Fatal Error: Migrations failed. Exiting.")
    sys.exit(1)

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

# ============================================================================
# BLUEPRINT REGISTRATION
# ============================================================================

# Initialize the database engine and limiter for all blueprints
from api.utils import set_engine, set_limiter
set_engine(engine)
set_limiter(limiter)

# Register blueprints
from api.auth_routes import auth_bp
from api.pluga_routes import pluga_bp
from api.soldier_routes import soldier_bp
from api.schedule_routes import schedule_bp
from api.ml_routes import ml_bp

app.register_blueprint(auth_bp)
app.register_blueprint(pluga_bp)
app.register_blueprint(soldier_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(ml_bp)

print("✅ All blueprints registered successfully")
print("   - Auth routes (register, login, me, users)")
print("   - Pluga routes (plugot, mahalkot, templates, constraints, join-requests)")
print("   - Soldier routes (soldiers, certifications, unavailable, status)")
print("   - Schedule routes (shavzakim, assignments, live-schedule)")
print("   - ML routes (train, smart-schedule, feedback, stats)")

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """בדיקת תקינות"""
    return jsonify({
        'status': 'healthy',
        'message': 'Shavzak API is running',
        'blueprints': ['auth', 'pluga', 'soldier', 'schedule', 'ml']
    }), 200


if __name__ == '__main__':
    print("🎖️  Shavzak API Server Starting...")
    print("=" * 70)
    print("📋 Database initialized")
    print("🔐 Authentication enabled")
    print("🔧 Flask Blueprints architecture")
    print("🚀 Server running on http://localhost:5000")
    print("=" * 70)

    import sys
    import atexit

    def cleanup_on_exit():
        """ניקוי resources בעת סגירת האפליקציה"""
        try:
            # סגור את כל ה-sessions הפתוחים
            from models import get_session
            print("\n🧹 ניקוי resources לפני סגירה...")

            # סגור את מנוע ה-DB
            if engine:
                engine.dispose()
                print("✅ מנוע DB נסגר בהצלחה")

            # flush stdout/stderr כדי למנוע lock
            sys.stdout.flush()
            sys.stderr.flush()

        except Exception as e:
            print(f"⚠️ שגיאה בניקוי: {e}")

    # רשום את פונקציית הניקוי
    atexit.register(cleanup_on_exit)

    # הרצת השרת
    try:
        # Use debug setting from config
        app.run(debug=app.config['DEBUG'], host=app.config['API_HOST'], port=app.config['API_PORT'], threaded=True)
    except KeyboardInterrupt:
        print("\n👋 Server shutting down...")
        cleanup_on_exit()
    finally:
        # ודא flush סופי
        sys.stdout.flush()
        sys.stderr.flush()
