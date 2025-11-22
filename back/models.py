"""
Database Models for Shavzak System
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date, Index, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import bcrypt

Base = declarative_base()

# תפקידים/הסמכות זמינים במערכת
# הסמכה = תפקיד נוסף שחייל יכול למלא
# חייל יכול לקבל מספר הסמכות (למשל: נהג + חמל)
#
# הסמכות לפי תפקיד:
# - לוחם: יכול לקבל נהג או חמל
# - מפקד (ממ, מכ, סמל): מקבל אוטומטית הסמכת "מפקד" + יכול לקבל "קצין תורן"
AVAILABLE_ROLES_CERTIFICATIONS = [
    'נהג',      # נהג - ללוחמים
    'חמל',      # חמל (מטה) - ללוחמים
    'מפקד',     # מפקד - ניתן אוטומטית למפקדים (ממ, מכ, סמל)
    'קצין תורן', # קצין תורן - מפקדים יכולים לקבל הסמכה זו
]

class User(Base):
    """משתמש במערכת"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # 'מפ', 'ממ', 'מכ'
    
    pluga_id = Column(Integer, ForeignKey('plugot.id'), nullable=True)
    mahlaka_id = Column(Integer, ForeignKey('mahalkot.id'), nullable=True)
    kita = Column(String(20), nullable=True)
    
    pluga = relationship("Pluga", back_populates="users")
    mahlaka = relationship("Mahlaka", back_populates="users")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def set_password(self, password):
        """הצפנת סיסמה"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """בדיקת סיסמה"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


class Pluga(Base):
    """פלוגה"""
    __tablename__ = 'plugot'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    gdud = Column(String(100))
    color = Column(String(20), default="#FFFFFF")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    mahalkot = relationship("Mahlaka", back_populates="pluga", cascade="all, delete-orphan")
    users = relationship("User", back_populates="pluga")
    assignment_templates = relationship("AssignmentTemplate", back_populates="pluga", cascade="all, delete-orphan")
    shavzakim = relationship("Shavzak", back_populates="pluga", cascade="all, delete-orphan")


class Mahlaka(Base):
    """מחלקה"""
    __tablename__ = 'mahalkot'
    
    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    color = Column(String(20), default="#FFFFFF")
    pluga_id = Column(Integer, ForeignKey('plugot.id'), nullable=False)
    
    pluga = relationship("Pluga", back_populates="mahalkot")
    soldiers = relationship("Soldier", back_populates="mahlaka", cascade="all, delete-orphan")
    users = relationship("User", back_populates="mahlaka")


class Soldier(Base):
    """חייל"""
    __tablename__ = 'soldiers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    idf_id = Column(String(20), unique=True, nullable=True)
    personal_id = Column(String(20), unique=True, nullable=True)
    
    role = Column(String(50), nullable=False)
    kita = Column(String(20), nullable=True)
    sex = Column(String(10))
    
    phone_number = Column(String(20))
    address = Column(Text)
    emergency_contact_name = Column(String(100))
    emergency_contact_number = Column(String(20))
    
    pakal = Column(String(50))
    recruit_date = Column(Date, nullable=True)
    birth_date = Column(Date, nullable=True)
    home_round_date = Column(Date, nullable=True)

    has_hatashab = Column(Boolean, default=False)
    hatash_2_days = Column(String(50), nullable=True)  # ימי התש"ב 2 קבועים (למשל: "1,2" עבור שני ושלישי, 0=ראשון)

    mahlaka_id = Column(Integer, ForeignKey('mahalkot.id'), nullable=False)
    
    mahlaka = relationship("Mahlaka", back_populates="soldiers")
    certifications = relationship("Certification", back_populates="soldier", cascade="all, delete-orphan")
    unavailable_dates = relationship("UnavailableDate", back_populates="soldier", cascade="all, delete-orphan")
    assignments = relationship("AssignmentSoldier", back_populates="soldier", cascade="all, delete-orphan")
    current_status = relationship("SoldierStatus", back_populates="soldier", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_soldier_mahlaka', 'mahlaka_id'),
        Index('idx_soldier_idf_id', 'idf_id'),
        Index('idx_soldier_role', 'role'),
    )


class Certification(Base):
    """
    הסמכות/תפקידים נוספים של חייל

    הסמכה = תפקיד נוסף שחייל יכול למלא במשימות
    לדוגמה:
    - חייל עם תפקיד "לוחם" יכול לקבל הסמכה "נהג" ולשמש כנהג במשימות
    - חייל עם תפקיד "מכ" יכול לקבל הסמכה "חמל" ולשמש בחמל
    - חייל עם תפקיד "לוחם" יכול לקבל הסמכה "מכ" ולפקד על כיתה

    רשימת התפקידים/הסמכות זמינה ב-AVAILABLE_ROLES_CERTIFICATIONS
    """
    __tablename__ = 'certifications'

    id = Column(Integer, primary_key=True)
    soldier_id = Column(Integer, ForeignKey('soldiers.id'), nullable=False)
    certification_name = Column(String(100), nullable=False)  # תפקיד נוסף מתוך AVAILABLE_ROLES_CERTIFICATIONS
    date_acquired = Column(Date, default=lambda: datetime.utcnow().date())

    soldier = relationship("Soldier", back_populates="certifications")


class UnavailableDate(Base):
    """תאריכים שבהם חייל לא זמין"""
    __tablename__ = 'unavailable_dates'

    id = Column(Integer, primary_key=True)
    soldier_id = Column(Integer, ForeignKey('soldiers.id'), nullable=False)
    date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # תאריך סיום (יחושב אוטומטית לגימלים וחק"שים)
    reason = Column(String(200))
    status = Column(String(20), default='approved')
    unavailability_type = Column(String(20), default='חופשה')  # 'חופשה', 'גימל', 'בקשת יציאה'
    quantity = Column(Integer, nullable=True)  # כמות גימלים/חק"שים

    soldier = relationship("Soldier", back_populates="unavailable_dates")


class SoldierStatus(Base):
    """סטטוס נוכחי של חייל"""
    __tablename__ = 'soldier_status'

    id = Column(Integer, primary_key=True)
    soldier_id = Column(Integer, ForeignKey('soldiers.id'), nullable=False, unique=True)

    # סטטוס: בבסיס, בקשת יציאה, גימלים, ריתוק, בסבב קו
    status_type = Column(String(50), default='בבסיס', nullable=False)

    # תאריך התחלה וסיום של הסטטוס
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # תאריך חזרה לבסיס (נשמר לתאימות לאחור)
    return_date = Column(Date, nullable=True)

    # הערות
    notes = Column(Text, nullable=True)

    # מתי עודכן לאחרונה
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    soldier = relationship("Soldier", back_populates="current_status", uselist=False)


class AssignmentTemplate(Base):
    """תבנית משימה"""
    __tablename__ = 'assignment_templates'

    id = Column(Integer, primary_key=True)
    pluga_id = Column(Integer, ForeignKey('plugot.id'), nullable=False)

    name = Column(String(100), nullable=False)
    assignment_type = Column(String(50), nullable=False)
    length_in_hours = Column(Integer, nullable=False)
    times_per_day = Column(Integer, nullable=False)
    start_hour = Column(Integer, nullable=True)  # שעת התחלה אופציונלית (0-23)

    commanders_needed = Column(Integer, default=0)
    drivers_needed = Column(Integer, default=0)
    soldiers_needed = Column(Integer, default=0)
    same_mahlaka_required = Column(Boolean, default=False)
    requires_certification = Column(String(100), nullable=True)
    requires_senior_commander = Column(Boolean, default=False)
    reuse_soldiers_for_standby = Column(Boolean, default=False)  # האם לקחת חיילים שסיימו משימה לכוננות

    pluga = relationship("Pluga", back_populates="assignment_templates")


class Shavzak(Base):
    """שיבוץ"""
    __tablename__ = 'shavzakim'
    
    id = Column(Integer, primary_key=True)
    pluga_id = Column(Integer, ForeignKey('plugot.id'), nullable=False)
    
    name = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    days_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    min_rest_hours = Column(Integer, default=8)
    emergency_mode = Column(Boolean, default=False)
    reuse_soldiers_for_standby = Column(Boolean, default=False)  # האם לאפשר שימוש חוזר בחיילים שסיימו משימה לכוננות

    pluga = relationship("Pluga", back_populates="shavzakim")
    assignments = relationship("Assignment", back_populates="shavzak", cascade="all, delete-orphan")


class Assignment(Base):
    """משימה ספציפית"""
    __tablename__ = 'assignments'

    id = Column(Integer, primary_key=True)
    shavzak_id = Column(Integer, ForeignKey('shavzakim.id'), nullable=False)

    name = Column(String(100), nullable=False)
    assignment_type = Column(String(50), nullable=False)
    day = Column(Integer, nullable=False)
    start_hour = Column(Integer, nullable=False)
    length_in_hours = Column(Integer, nullable=False)

    assigned_mahlaka_id = Column(Integer, ForeignKey('mahalkot.id'), nullable=True)

    shavzak = relationship("Shavzak", back_populates="assignments")
    assigned_mahlaka = relationship("Mahlaka")
    soldiers_assigned = relationship("AssignmentSoldier", back_populates="assignment", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_assignment_shavzak', 'shavzak_id'),
        Index('idx_assignment_day', 'day'),
        Index('idx_assignment_type', 'assignment_type'),
    )


class AssignmentSoldier(Base):
    """קישור בין משימה לחייל"""
    __tablename__ = 'assignment_soldiers'

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id'), nullable=False)
    soldier_id = Column(Integer, ForeignKey('soldiers.id'), nullable=False)
    role_in_assignment = Column(String(50), nullable=False)

    assignment = relationship("Assignment", back_populates="soldiers_assigned")
    soldier = relationship("Soldier", back_populates="assignments")


class JoinRequest(Base):
    """בקשת הצטרפות למפ חדש"""
    __tablename__ = 'join_requests'

    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    pluga_name = Column(String(100), nullable=False)
    gdud = Column(String(100), nullable=True)

    status = Column(String(20), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    def set_password(self, password):
        """הצפנת סיסמה"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


class SchedulingConstraint(Base):
    """אילוצי שיבוץ"""
    __tablename__ = 'scheduling_constraints'

    id = Column(Integer, primary_key=True)
    pluga_id = Column(Integer, ForeignKey('plugot.id'), nullable=False)
    mahlaka_id = Column(Integer, ForeignKey('mahalkot.id'), nullable=True)  # אם None, חל על כל הפלוגה

    constraint_type = Column(String(50), nullable=False)  # 'cannot_assign', 'max_assignments_per_day', 'restricted_hours'
    assignment_type = Column(String(50), nullable=True)  # אם None, חל על כל סוגי המשימות

    # ערכים נוספים (JSON או ערך בודד)
    constraint_value = Column(String(255), nullable=True)  # למשל: "3" עבור max_assignments, או "22-06" עבור restricted_hours

    days_of_week = Column(String(50), nullable=True)  # למשל: "0,1,2" (ראשון, שני, שלישי)
    start_date = Column(Date, nullable=True)  # תאריך התחלה (אופציונלי)
    end_date = Column(Date, nullable=True)  # תאריך סיום (אופציונלי)

    reason = Column(Text, nullable=True)  # סיבה/הערה
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    pluga = relationship("Pluga", foreign_keys=[pluga_id])
    mahlaka = relationship("Mahlaka", foreign_keys=[mahlaka_id])


class ScheduleIteration(Base):
    """איטרציה של שיבוץ - כל ניסיון ליצור שיבוץ"""
    __tablename__ = 'schedule_iterations'

    id = Column(Integer, primary_key=True)
    shavzak_id = Column(Integer, ForeignKey('shavzakim.id'), nullable=False)
    iteration_number = Column(Integer, nullable=False)  # מספר הניסיון (1, 2, 3...)

    # האם זו האיטרציה הפעילה הנוכחית
    is_active = Column(Boolean, default=True)

    # מצב האיטרציה
    status = Column(String(20), default='pending')  # 'pending', 'approved', 'rejected', 'superseded'

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # קישור לשיבוץ המקורי
    shavzak = relationship("Shavzak")

    # היסטוריית הפידבקים על האיטרציה הזו
    feedbacks = relationship("FeedbackHistory", back_populates="iteration", cascade="all, delete-orphan")


class FeedbackHistory(Base):
    """היסטוריית פידבק על שיבוצים"""
    __tablename__ = 'feedback_history'

    id = Column(Integer, primary_key=True)
    shavzak_id = Column(Integer, ForeignKey('shavzakim.id'), nullable=False)
    iteration_id = Column(Integer, ForeignKey('schedule_iterations.id'), nullable=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id'), nullable=True)

    # פרטי הפידבק
    rating = Column(String(20), nullable=False)  # 'approved', 'rejected', 'modified'
    feedback_text = Column(Text, nullable=True)  # הסבר מילולי

    # שינויים שבוצעו (JSON)
    changes = Column(Text, nullable=True)  # JSON של השינויים שהמשתמש ביקש

    # מי נתן את הפידבק
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # מתי
    created_at = Column(DateTime, default=datetime.utcnow)

    # האם הפידבק הזה גרם ליצירת איטרציה חדשה
    triggered_new_iteration = Column(Boolean, default=False)

    # קישורים
    shavzak = relationship("Shavzak")
    iteration = relationship("ScheduleIteration", back_populates="feedbacks")
    assignment = relationship("Assignment")
    user = relationship("User")

    __table_args__ = (
        Index('idx_feedback_shavzak', 'shavzak_id'),
        Index('idx_feedback_rating', 'rating'),
        Index('idx_feedback_created_at', 'created_at'),
    )


class ConstraintFeedback(Base):
    """פידבק על אילוצים שלא התקיימו"""
    __tablename__ = 'constraint_feedbacks'

    id = Column(Integer, primary_key=True)
    constraint_id = Column(Integer, ForeignKey('scheduling_constraints.id'), nullable=False)
    violated_assignment_id = Column(Integer, ForeignKey('assignments.id'), nullable=False)
    good_example_assignment_id = Column(Integer, ForeignKey('assignments.id'), nullable=True)

    # מי דיווח
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # הערות
    notes = Column(Text, nullable=True)

    # מתי
    created_at = Column(DateTime, default=datetime.utcnow)

    # קישורים
    constraint = relationship("SchedulingConstraint")
    violated_assignment = relationship("Assignment", foreign_keys=[violated_assignment_id])
    good_example_assignment = relationship("Assignment", foreign_keys=[good_example_assignment_id])
    user = relationship("User")


def init_db(db_path='shavzak.db'):
    """אתחול מסד הנתונים"""
    # הגדלת timeout ל-30 שניות (במקום 5 ברירת מחדל)
    engine = create_engine(f'sqlite:///{db_path}', echo=False, connect_args={'timeout': 30})
    
    # הפעלת WAL mode לביצועים טובים יותר ומניעת נעילות
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """יצירת session"""
    Session = sessionmaker(bind=engine)
    return Session()
