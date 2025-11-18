"""
Shared utilities for API routes
פונקציות עזר משותפות לכל ה-routes
"""
from models import get_session
import os

# Get the DB engine (will be set by main api.py)
engine = None

def set_engine(db_engine):
    """Set the database engine for all blueprints"""
    global engine
    engine = db_engine

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
