"""
Configuration file for Shavzak System
"""
import os

class Config:
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'shavzak.db')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_DAYS = 7
    
    # API Settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Scheduling defaults
    DEFAULT_MIN_REST_HOURS = 8
    DEFAULT_EMERGENCY_REST_HOURS = 4
    
    # Role definitions
    ROLES = {
        'מפ': {
            'name': 'מפקד פלוגה',
            'level': 3,
            'permissions': ['all']
        },
        'ממ': {
            'name': 'מפקד מחלקה',
            'level': 2,
            'permissions': ['view_all', 'edit_mahlaka', 'create_shavzak']
        },
        'מכ': {
            'name': 'מפקד כיתה',
            'level': 1,
            'permissions': ['view_all', 'edit_kita']
        }
    }
    
    # Assignment type definitions
    ASSIGNMENT_TYPES = [
        'סיור',
        'שמירה',
        'כוננות א',
        'כוננות ב',
        'חמל',
        'תורן מטבח',
        'חפק גשש',
        'שלז',
        'קצין תורן'
    ]
    
    # Role types for soldiers
    SOLDIER_ROLES = [
        'לוחם',
        'נהג',
        'ממ',
        'מכ',
        'סמל'
    ]
    
    # Certifications
    CERTIFICATIONS = [
        'חמל',
        'נהג',
        'מדריך',
        'סייר',
        'קצונה'
    ]
