"""
Configuration for Shavzak System
"""
import os

class Config:
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'shavzak.db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_DAYS = 7
    
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5000))
    # Security: Default to False in production unless explicitly enabled
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Check for weak secret key in production
    if not DEBUG and SECRET_KEY == 'your-secret-key-change-in-production':
        raise ValueError("CRITICAL SECURITY ERROR: You are running in production (DEBUG=False) with the default SECRET_KEY. Please set the SECRET_KEY environment variable.")
    
    # Ditto Configuration
    DITTO_API_URL = os.getenv('DITTO_API_URL', 'https://{YOUR_APP_ID}.cloud.ditto.live')
    DITTO_API_KEY = os.getenv('DITTO_API_KEY', '')

    DEFAULT_MIN_REST_HOURS = 8
    DEFAULT_EMERGENCY_REST_HOURS = 4
