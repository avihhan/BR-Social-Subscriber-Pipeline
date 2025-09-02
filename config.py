import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Google Sheets
    GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Subscriber Pipeline')
    
    # EmailJS Configuration
    EMAILJS_SERVICE_ID = os.getenv('EMAILJS_SERVICE_ID')
    EMAILJS_TEMPLATE_ID = os.getenv('EMAILJS_TEMPLATE_ID')
    EMAILJS_USER_ID = os.getenv('EMAILJS_USER_ID')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # IP Geolocation API
    IP_API_URL = 'http://ip-api.com/json/'