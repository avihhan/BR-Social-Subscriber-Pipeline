import os
import json
from flask import Flask, request, jsonify
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

# Initialize Flask app
app = Flask(__name__)

# Google Sheets setup
def init_google_sheets():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('google-credentials.json', scope)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        print(f"Error initializing Google Sheets: {e}")
        return None

# IP location function
def get_ip_location(ip_address):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=3)
        if response.status_code == 200:
            data = response.json()
            return {
                'country': data.get('country', ''),
                'region': data.get('regionName', ''),
                'city': data.get('city', ''),
                'lat': data.get('lat', 0),
                'lon': data.get('lon', 0)
            }
    except Exception as e:
        print(f"Error getting IP location: {e}")
    return {'country': '', 'region': '', 'city': '', 'lat': 0, 'lon': 0}

# Email sending function
def send_email_smtp(to_email, to_name, subject, html_content, advertisement_html):
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', smtp_username)
        from_name = os.getenv('FROM_NAME', 'Subscriber Pipeline')
        
        if not all([smtp_username, smtp_password]):
            raise Exception("SMTP credentials not configured")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = f"{to_name} <{to_email}>"
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            {html_content}
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            
            {advertisement_html}
            
            <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; font-size: 12px; color: #666;">
                <p>You received this email because you subscribed to our newsletter.</p>
                <p>To unsubscribe, please reply with "UNSUBSCRIBE" in the subject line.</p>
            </div>
        </body>
        </html>
        """
        
        html_part = MIMEText(full_html, 'html', 'utf-8')
        msg.attach(html_part)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Cloud Function entry point
def subscriber_pipeline(request):
    """Main Cloud Function entry point"""
    # Set CORS headers
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    # Route the request based on path
    path = request.path
    method = request.method
    
    try:
        if path == '/subscribe' and method == 'POST':
            return handle_subscribe(request, headers)
        elif path == '/send-template-email' and method == 'POST':
            return handle_send_template_email(request, headers)
        elif path == '/subscribers' and method == 'GET':
            return handle_get_subscribers(request, headers)
        elif path == '/unsubscribe' and method == 'POST':
            return handle_unsubscribe(request, headers)
        elif path == '/health' and method == 'GET':
            return handle_health(request, headers)
        else:
            return (jsonify({'error': 'Endpoint not found'}), 404, headers)
    
    except Exception as e:
        return (jsonify({'error': str(e)}), 500, headers)

def handle_subscribe(request, headers):
    """Handle subscriber registration"""
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    
    if not name or not email:
        return (jsonify({'error': 'Name and email are required'}), 400, headers)
    
    ip_address = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0]
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    location_data = get_ip_location(ip_address)
    
    client = init_google_sheets()
    if not client:
        return (jsonify({'error': 'Failed to connect to Google Sheets'}), 500, headers)
    
    spreadsheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Subscriber List')
    try:
        spreadsheet = client.open(spreadsheet_name)
        sheet = spreadsheet.sheet1
    except Exception as e:
        return (jsonify({'error': f'Error accessing Google Sheet: {str(e)}'}), 500, headers)
    
    # Check for duplicate email
    normalized_email = email.strip().lower()
    email_column_index = 2
    all_emails = sheet.col_values(email_column_index)
    
    if normalized_email in [e.lower() for e in all_emails]:
        existing_record = None
        for row_idx, row_data in enumerate(sheet.get_all_records(), start=2):
            if row_data.get('Email', '').lower() == normalized_email:
                existing_record = row_data
                break
        
        if existing_record:
            return (jsonify({
                'message': 'already subscribed',
                'data': {
                    'name': existing_record.get('Name'),
                    'email': existing_record.get('Email'),
                    'timestamp': existing_record.get('Timestamp')
                }
            }), 200, headers)
    
    # Add subscriber
    row_data = [
        name.strip().lower(),
        normalized_email,
        timestamp,
        ip_address.strip().lower(),
        location_data.get('country', '').strip().lower(),
        location_data.get('region', '').strip().lower(),
        location_data.get('city', '').strip().lower(),
        location_data.get('lat', 0),
        location_data.get('lon', 0)
    ]
    
    sheet.append_row(row_data)
    
    return (jsonify({
        'message': 'Subscriber added successfully',
        'data': {
            'name': name,
            'email': email,
            'timestamp': timestamp,
            'ip_address': ip_address,
            'location': location_data
        }
    }), 201, headers)

def handle_send_template_email(request, headers):
    """Handle sending template emails"""
    data = request.get_json()
    template_name = data.get('template_name')
    subject = data.get('subject')
    advertisement_html = data.get('advertisement_html', '')
    
    if not template_name or not subject:
        return (jsonify({'error': 'Template name and subject are required'}), 400, headers)
    
    client = init_google_sheets()
    if not client:
        return (jsonify({'error': 'Failed to connect to Google Sheets'}), 500, headers)
    
    spreadsheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Subscriber List')
    try:
        spreadsheet = client.open(spreadsheet_name)
        sheet = spreadsheet.sheet1
    except Exception as e:
        return (jsonify({'error': f'Error accessing Google Sheet: {str(e)}'}), 500, headers)
    
    # Get all subscribers
    subscribers = sheet.get_all_records()
    if not subscribers:
        return (jsonify({'error': 'No subscribers found'}), 404, headers)
    
    # Load template
    try:
        with open(f'templates/{template_name}', 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        return (jsonify({'error': f'Error loading template: {str(e)}'}), 500, headers)
    
    # Send emails
    success_count = 0
    failed_count = 0
    
    for subscriber in subscribers:
        name = subscriber.get('Name', 'Subscriber')
        email = subscriber.get('Email', '')
        
        if email:
            # Personalize template
            personalized_content = template_content.replace('{{name}}', name)
            
            if send_email_smtp(email, name, subject, personalized_content, advertisement_html):
                success_count += 1
            else:
                failed_count += 1
    
    return (jsonify({
        'message': 'Email campaign completed',
        'success_count': success_count,
        'failed_count': failed_count
    }), 200, headers)

def handle_get_subscribers(request, headers):
    """Handle getting subscribers with filters"""
    client = init_google_sheets()
    if not client:
        return (jsonify({'error': 'Failed to connect to Google Sheets'}), 500, headers)
    
    spreadsheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Subscriber List')
    try:
        spreadsheet = client.open(spreadsheet_name)
        sheet = spreadsheet.sheet1
    except Exception as e:
        return (jsonify({'error': f'Error accessing Google Sheet: {str(e)}'}), 500, headers)
    
    subscribers = sheet.get_all_records()
    return (jsonify({'subscribers': subscribers}), 200, headers)

def handle_unsubscribe(request, headers):
    """Handle unsubscribing users"""
    data = request.get_json()
    email_to_delete = data.get('email')
    
    if not email_to_delete:
        return (jsonify({'error': 'Email is required for unsubscription'}), 400, headers)
    
    normalized_email_to_delete = email_to_delete.strip().lower()
    
    client = init_google_sheets()
    if not client:
        return (jsonify({'error': 'Failed to connect to Google Sheets'}), 500, headers)
    
    spreadsheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Subscriber List')
    try:
        spreadsheet = client.open(spreadsheet_name)
        sheet = spreadsheet.sheet1
    except Exception as e:
        return (jsonify({'error': f'Error accessing Google Sheet: {str(e)}'}), 500, headers)
    
    email_column_index = 2
    all_emails = sheet.col_values(email_column_index)
    
    row_to_delete_index = -1
    deleted_row_data = {}
    
    for i, email_in_sheet in enumerate(all_emails):
        if email_in_sheet.strip().lower() == normalized_email_to_delete:
            row_to_delete_index = i + 1
            deleted_row_data = sheet.row_values(row_to_delete_index)
            break
    
    if row_to_delete_index != -1:
        sheet.delete_rows(row_to_delete_index)
        return (jsonify({
            'message': 'unsubscribed successfully',
            'data': {
                'email': normalized_email_to_delete,
                'deleted_row_content': deleted_row_data
            }
        }), 200, headers)
    else:
        return (jsonify({'message': 'email not found'}), 404, headers)

def handle_health(request, headers):
    """Health check endpoint"""
    return (jsonify({'status': 'healthy', 'message': 'Subscriber Pipeline is running'}), 200, headers)

# For local testing (optional)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)