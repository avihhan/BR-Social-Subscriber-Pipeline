from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import json
from datetime import datetime
import os
import smtplib

# Robust email import handling for Python 3.13 compatibility
try:
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.header import Header
    EMAIL_HTML_AVAILABLE = True
    HEADER_AVAILABLE = True
    print("✅ Advanced email modules loaded successfully")
except ImportError as e:
    print(f"⚠️ Warning: Advanced email modules not available: {e}")
    print("Using basic email functionality")
    EMAIL_HTML_AVAILABLE = False
    HEADER_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Google Sheets configuration
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Initialize Google Sheets client
def init_google_sheets():
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'google-credentials.json', SCOPES)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        print(f"Error initializing Google Sheets: {e}")
        return None

# Send email using SMTP (robust version with fallback)
def send_email_smtp(to_email, to_name, subject, html_content, advertisement_html):
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', smtp_username)
        from_name = os.getenv('FROM_NAME', 'Subscriber Pipeline')
        
        if not all([smtp_username, smtp_password]):
            raise Exception("SMTP credentials not configured")
        
        # ALWAYS send HTML email - no more plain text fallback
        try:
            # Try to use advanced email modules first
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = f"{to_name} <{to_email}>"
            
            # Combine HTML content with advertisement
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
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {to_email} using advanced modules")
            
        except Exception as e:
            print(f"⚠️ Advanced modules failed, trying basic HTML: {e}")
            
            # Fallback: send basic HTML email using raw SMTP (NO MORE PLAIN TEXT)
            # Use Header if available, otherwise use plain subject
            if HEADER_AVAILABLE:
                safe_subject = Header(subject, 'utf-8')
            else:
                safe_subject = subject
            
            message = f"""From: {from_name} <{from_email}>
To: {to_name} <{to_email}>
Subject: {safe_subject}
MIME-Version: 1.0
Content-Type: text/html; charset=utf-8

{html_content}

<hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">

{advertisement_html}

<div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; font-size: 12px; color: #666;">
    <p>You received this email because you subscribed to our newsletter.</p>
    <p>To unsubscribe, please reply with "UNSUBSCRIBE" in the subject line.</p>
</div>
"""
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(from_email, to_email, message)
            
            print(f"✅ Email sent successfully to {to_email} using basic HTML")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending email to {to_email}: {e}")
        return False


# Get IP geolocation
def get_ip_location(ip_address):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return {
                'country': data.get('country', 'Unknown'),
                'region': data.get('regionName', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'lat': data.get('lat', 0),
                'lon': data.get('lon', 0)
            }
    except Exception as e:
        print(f"Error getting IP location: {e}")
    
    return {'country': 'Unknown', 'region': 'Unknown', 'city': 'Unknown', 'lat': 0, 'lon': 0}

# Add this function to your app.py
def load_html_template(template_name, **kwargs):
    """Load HTML template and replace placeholders"""
    try:
        template_path = f"templates/{template_name}.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Replace placeholders
        for key, value in kwargs.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))
        
        return html_content
    except Exception as e:
        print(f"Error loading template {template_name}: {e}")
        return f"<h1>Hello {kwargs.get('name', 'there')}!</h1><p>Welcome to our newsletter!</p>"


@app.route('/subscribe', methods=['POST'])
def subscribe():
    """Endpoint to add new subscribers"""
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        
        if not name or not email:
            return jsonify({'error': 'Name and email are required'}), 400
        
        # Get client IP
        ip_address = request.remote_addr
        if request.headers.get('X-Forwarded-For'):
            ip_address = request.headers.get('X-Forwarded-For').split(',')[0]
        
        # Get timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get IP location
        location_data = get_ip_location(ip_address)
        
        # Initialize Google Sheets
        client = init_google_sheets()
        if not client:
            return jsonify({'error': 'Failed to connect to Google Sheets'}), 500
        
        # Open the spreadsheet - BETTER ERROR HANDLING
        spreadsheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Subscriber List')
        try:
            spreadsheet = client.open(spreadsheet_name)
            sheet = spreadsheet.sheet1
            print(f"✅ Successfully opened existing sheet: {spreadsheet_name}")
        except gspread.SpreadsheetNotFound:
            return jsonify({
                'error': f'Spreadsheet "{spreadsheet_name}" not found. Please create it manually and share with the service account.'
            }), 404
        except Exception as e:
            return jsonify({
                'error': f'Error accessing Google Sheet: {str(e)}'
            }), 500
        
        # Normalize inputs
        normalized_name = (name or "").strip().lower()
        normalized_email = (email or "").strip().lower()
        normalized_ip = (ip_address or "").strip().lower()

        # Fast duplicate check using email column (col 2)
        try:
            email_column = sheet.col_values(2)  # includes header
            # Find first match ignoring header
            match_index = next((i for i, v in enumerate(email_column) if i > 0 and (v or '').strip().lower() == normalized_email), None)
            if match_index is not None:
                # Row index in sheet is match_index + 1
                row_idx = match_index + 1
                row_vals = sheet.row_values(row_idx)
                # Expect headers: Name, Email, Timestamp, IP Address, Country, Region, City, Latitude, Longitude
                stored_name = row_vals[0] if len(row_vals) > 0 else ''
                stored_email = row_vals[1] if len(row_vals) > 1 else ''
                stored_timestamp = row_vals[2] if len(row_vals) > 2 else ''
                return jsonify({
                    'message': 'already subscribed',
                    'data': {
                        'name': stored_name,
                        'email': stored_email,
                        'timestamp': stored_timestamp
                    }
                }), 200
        except Exception as e:
            print(f"Warning: failed to check duplicates quickly: {e}")

        # Add subscriber data
        row_data = [
            normalized_name,
            normalized_email,
            timestamp,  # keep original case/format
            normalized_ip,
            (location_data.get('country', '') or "").strip().lower(),
            (location_data.get('region', '') or "").strip().lower(),
            (location_data.get('city', '') or "").strip().lower(),
            location_data.get('lat', 0),
            location_data.get('lon', 0)
        ]
        
        sheet.append_row(row_data)
        
        return jsonify({
            'message': 'Subscriber added successfully',
            'data': {
                'name': name,
                'email': email,
                'timestamp': timestamp,
                'ip_address': ip_address,
                'location': location_data
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add a new endpoint to send emails with HTML templates
@app.route('/send-template-email', methods=['POST'])
def send_template_email():
    """Send email using HTML template"""
    try:
        data = request.get_json()
        template_name = data.get('template_name', 'welcome')
        subject = data.get('subject', 'Newsletter')
        
        # Initialize Google Sheets
        client = init_google_sheets()
        if not client:
            return jsonify({'error': 'Failed to connect to Google Sheets'}), 500
        
        # Get subscribers
        sheet = client.open(os.getenv('GOOGLE_SHEET_NAME', 'Subscriber List')).sheet1
        all_records = sheet.get_all_records()
        
        # Filter out header row
        subscribers = [record for record in all_records if record.get('Name') != 'Name']
        
        if not subscribers:
            return jsonify({'message': 'No subscribers found'}), 200
        
        # Send emails
        sent_count = 0
        failed_count = 0
        
        for subscriber in subscribers:
            try:
                # Load HTML template with subscriber data
                html_content = load_html_template(
                    template_name,
                    name=subscriber['Name'],
                    email=subscriber['Email'],
                    city=subscriber.get('City', ''),
                    country=subscriber.get('Country', '')
                )
                
                # Send email
                success = send_email_smtp(
                    subscriber['Email'],
                    subscriber['Name'],
                    subject,
                    html_content,
                    ""  # No advertisement for template emails
                )
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"Failed to send email to {subscriber['Email']}: {e}")
                failed_count += 1
        
        return jsonify({
            'message': 'Template email campaign completed',
            'template_used': template_name,
            'total_subscribers': len(subscribers),
            'sent_count': sent_count,
            'failed_count': failed_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/subscribers', methods=['GET'])
def get_subscribers():
    """Get all subscribers with optional filtering"""
    try:
        # Query parameters for filtering
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        country = request.args.get('country')
        region = request.args.get('region')
        city = request.args.get('city')
        
        # Initialize Google Sheets
        client = init_google_sheets()
        if not client:
            return jsonify({'error': 'Failed to connect to Google Sheets'}), 500
        
        # Get subscribers
        sheet = client.open(os.getenv('GOOGLE_SHEET_NAME', 'Subscriber List')).sheet1
        all_records = sheet.get_all_records()
        
        # Filter if parameters provided
        if any([start_date, end_date, country, region, city]):
            filtered_records = []
            
            for record in all_records:
                # Skip header row
                if record.get('Name') == 'Name':
                    continue
                
                # Apply filters
                if start_date and end_date:
                    try:
                        record_date = datetime.strptime(record.get('Timestamp', '').split()[0], '%Y-%m-%d')
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        
                        if not (start_dt <= record_date <= end_dt):
                            continue
                    except:
                        continue
                
                if country and record.get('Country') != country:
                    continue
                if region and record.get('Region') != region:
                    continue
                if city and record.get('City') != city:
                    continue
                
                filtered_records.append(record)
            
            all_records = filtered_records
        
        return jsonify({
            'subscribers': all_records,
            'count': len(all_records)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    """Remove a subscriber by email"""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        if not email:
            return jsonify({'error': 'email is required'}), 400

        # Initialize Google Sheets
        client = init_google_sheets()
        if not client:
            return jsonify({'error': 'Failed to connect to Google Sheets'}), 500

        # Open the spreadsheet
        spreadsheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Subscriber List')
        try:
            spreadsheet = client.open(spreadsheet_name)
            sheet = spreadsheet.sheet1
        except gspread.SpreadsheetNotFound:
            return jsonify({'error': f'Spreadsheet "{spreadsheet_name}" not found'}), 404
        except Exception as e:
            return jsonify({'error': f'Error accessing Google Sheet: {str(e)}'}), 500

        # Fetch all records and locate the row to delete
        records = sheet.get_all_records()
        delete_row_index = None
        matched_record = None
        for idx, record in enumerate(records):
            record_email = (record.get('Email', '') or '').strip().lower()
            if record_email == email:
                # gspread rows are 1-indexed and include header row; records start at row 2
                delete_row_index = idx + 2
                matched_record = record
                break

        if not delete_row_index:
            return jsonify({'message': 'email not found'}), 404

        # Delete the row
        sheet.delete_rows(delete_row_index)

        return jsonify({
            'message': 'unsubscribed successfully',
            'data': {
                'email': matched_record.get('Email', ''),
                'name': matched_record.get('Name', ''),
                'timestamp': matched_record.get('Timestamp', ''),
                'deleted_row': delete_row_index
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, host='0.0.0.0', port=8000)