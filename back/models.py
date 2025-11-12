"""
Database Models for Shavzak System
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import bcrypt

Base = declarative_base()

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
    
    is_platoon_commander = Column(Boolean, default=False)
    has_hatashab = Column(Boolean, default=False)
    
    mahlaka_id = Column(Integer, ForeignKey('mahalkot.id'), nullable=False)
    
    mahlaka = relationship("Mahlaka", back_populates="soldiers")
    certifications = relationship("Certification", back_populates="soldier", cascade="all, delete-orphan")
    unavailable_dates = relationship("UnavailableDate", back_populates="soldier", cascade="all, delete-orphan")
    assignments = relationship("AssignmentSoldier", back_populates="soldier", cascade="all, delete-orphan")


class Certification(Base):
    """הסמכות חייל"""
    __tablename__ = 'certifications'
    
    id = Column(Integer, primary_key=True)
    soldier_id = Column(Integer, ForeignKey('soldiers.id'), nullable=False)
    certification_name = Column(String(100), nullable=False)
    date_acquired = Column(Date, default=datetime.utcnow)
    
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
    unavailability_type = Column(String(20), default='חופשה')  # 'חופשה', 'גימל', 'חק"צ'
    quantity = Column(Integer, nullable=True)  # כמות גימלים/חק"שים

    soldier = relationship("Soldier", back_populates="unavailable_dates")


class AssignmentTemplate(Base):
    """תבנית משימה"""
    __tablename__ = 'assignment_templates'
    
    id = Column(Integer, primary_key=True)
    pluga_id = Column(Integer, ForeignKey('plugot.id'), nullable=False)
    
    name = Column(String(100), nullable=False)
    assignment_type = Column(String(50), nullable=False)
    length_in_hours = Column(Integer, nullable=False)
    times_per_day = Column(Integer, nullable=False)
    
    commanders_needed = Column(Integer, default=0)
    drivers_needed = Column(Integer, default=0)
    soldiers_needed = Column(Integer, default=0)
    same_mahlaka_required = Column(Boolean, default=False)
    requires_certification = Column(String(100), nullable=True)
    requires_senior_commander = Column(Boolean, default=False)
    
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


def init_db(db_path='shavzak.db'):
    """אתחול מסד הנתונים"""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """יצירת session"""
    Session = sessionmaker(bind=engine)
    return Session()
