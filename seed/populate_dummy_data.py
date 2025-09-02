'''
This script is used to populate the Google Sheet with dummy subscriber data

Usage:
python populate_dummy_data.py
'''

import sys
import os

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import random
import time

def populate_dummy_data():
    """Populate Google Sheet with dummy subscriber data"""
    
    # Define the scope
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        # Load credentials using absolute path to project root
        credentials_path = os.path.join(PROJECT_ROOT, 'google-credentials.json')
        print(f"🔍 Looking for credentials at: {credentials_path}")
        
        if not os.path.exists(credentials_path):
            print(f"❌ Credentials file not found at: {credentials_path}")
            return
        
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, SCOPES)
        client = gspread.authorize(credentials)
        
        # Open the spreadsheet
        spreadsheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Subscriber List')
        
        try:
            spreadsheet = client.open(spreadsheet_name)
            print(f"✅ Opened existing spreadsheet: {spreadsheet_name}")
        except gspread.SpreadsheetNotFound:
            print(f"❌ Spreadsheet '{spreadsheet_name}' not found!")
            print("Please create a Google Sheet manually and share it with your service account.")
            print(f"Service account email: {credentials.service_account_email}")
            print("Then run this script again.")
            return
        
        sheet = spreadsheet.sheet1
        
        print(f" Sheet URL: {spreadsheet.url}")
        
        # Sample data for different locations and time periods
        dummy_subscribers = [
            # US Subscribers
            {
                'name': 'John Smith',
                'email': 'john.smith@example.com',
                'country': 'United States',
                'region': 'California',
                'city': 'San Francisco',
                'lat': 37.7749,
                'lon': -122.4194
            },
            {
                'name': 'Sarah Johnson',
                'email': 'sarah.johnson@example.com',
                'country': 'United States',
                'region': 'New York',
                'city': 'New York City',
                'lat': 40.7128,
                'lon': -74.0060
            },
            {
                'name': 'Michael Brown',
                'email': 'michael.brown@example.com',
                'country': 'United States',
                'region': 'Texas',
                'city': 'Austin',
                'lat': 30.2672,
                'lon': -97.7431
            },
            {
                'name': 'Emily Davis',
                'email': 'emily.davis@example.com',
                'country': 'United States',
                'region': 'Florida',
                'city': 'Miami',
                'lat': 25.7617,
                'lon': -80.1918
            },
            {
                'name': 'David Wilson',
                'email': 'david.wilson@example.com',
                'country': 'United States',
                'region': 'Washington',
                'city': 'Seattle',
                'lat': 47.6062,
                'lon': -122.3321
            },
            
            # Canadian Subscribers
            {
                'name': 'Emma Thompson',
                'email': 'emma.thompson@example.com',
                'country': 'Canada',
                'region': 'Ontario',
                'city': 'Toronto',
                'lat': 43.6532,
                'lon': -79.3832
            },
            {
                'name': 'James Anderson',
                'email': 'james.anderson@example.com',
                'country': 'Canada',
                'region': 'Quebec',
                'city': 'Montreal',
                'lat': 45.5017,
                'lon': -73.5673
            },
            {
                'name': 'Olivia Martinez',
                'email': 'olivia.martinez@example.com',
                'country': 'Canada',
                'region': 'British Columbia',
                'city': 'Vancouver',
                'lat': 49.2827,
                'lon': -123.1207
            },
            
            # UK Subscribers
            {
                'name': 'William Taylor',
                'email': 'william.taylor@example.com',
                'country': 'United Kingdom',
                'region': 'England',
                'city': 'London',
                'lat': 51.5074,
                'lon': -0.1278
            },
            {
                'name': 'Sophia Garcia',
                'email': 'sophia.garcia@example.com',
                'country': 'United Kingdom',
                'region': 'Scotland',
                'city': 'Edinburgh',
                'lat': 55.9533,
                'lon': -3.1883
            },
            {
                'name': 'Daniel Rodriguez',
                'email': 'daniel.rodriguez@example.com',
                'country': 'United Kingdom',
                'region': 'Wales',
                'city': 'Cardiff',
                'lat': 51.4816,
                'lon': -3.1791
            },
            
            # Australian Subscribers
            {
                'name': 'Isabella Lewis',
                'email': 'isabella.lewis@example.com',
                'country': 'Australia',
                'region': 'New South Wales',
                'city': 'Sydney',
                'lat': -33.8688,
                'lon': 151.2093
            },
            {
                'name': 'Ethan Lee',
                'email': 'ethan.lee@example.com',
                'country': 'Australia',
                'region': 'Victoria',
                'city': 'Melbourne',
                'lat': -37.8136,
                'lon': 144.9631
            },
            
            # German Subscribers
            {
                'name': 'Ava Walker',
                'email': 'ava.walker@example.com',
                'country': 'Germany',
                'region': 'Berlin',
                'city': 'Berlin',
                'lat': 52.5200,
                'lon': 13.4050
            },
            {
                'name': 'Noah Hall',
                'email': 'noah.hall@example.com',
                'country': 'Germany',
                'region': 'Bavaria',
                'city': 'Munich',
                'lat': 48.1351,
                'lon': 11.5820
            },
            
            # Indian Subscribers
            {
                'name': 'Mia Allen',
                'email': 'mia.allen@example.com',
                'country': 'India',
                'region': 'Maharashtra',
                'city': 'Mumbai',
                'lat': 19.0760,
                'lon': 72.8777
            },
            {
                'name': 'Lucas Young',
                'email': 'lucas.young@example.com',
                'country': 'India',
                'region': 'Delhi',
                'city': 'New Delhi',
                'lat': 28.6139,
                'lon': 77.2090
            },
            
            # Japanese Subscribers
            {
                'name': 'Aria King',
                'email': 'aria.king@example.com',
                'country': 'Japan',
                'region': 'Tokyo',
                'city': 'Tokyo',
                'lat': 35.6762,
                'lon': 139.6503
            },
            {
                'name': 'Grayson Wright',
                'email': 'grayson.wright@example.com',
                'country': 'Japan',
                'region': 'Osaka',
                'city': 'Osaka',
                'lat': 34.6937,
                'lon': 135.5023
            }
        ]
        
        print(f"\n📝 Adding {len(dummy_subscribers)} dummy subscribers...")
        
        # Generate timestamps over the last 30 days
        base_date = datetime.now() - timedelta(days=30)
        
        for i, subscriber in enumerate(dummy_subscribers):
            try:
                # Generate random timestamp within last 30 days
                random_days = random.randint(0, 30)
                random_hours = random.randint(0, 23)
                random_minutes = random.randint(0, 59)
                
                timestamp = base_date + timedelta(
                    days=random_days,
                    hours=random_hours,
                    minutes=random_minutes
                )
                
                # Generate random IP address
                ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
                
                # Prepare row data
                row_data = [
                    (subscriber['name'] or "").strip().lower(),
                    (subscriber['email'] or "").strip().lower(),
                    timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    (ip_address or "").strip().lower(),
                    (subscriber['country'] or "").strip().lower(),
                    (subscriber['region'] or "").strip().lower(),
                    (subscriber['city'] or "").strip().lower(),
                    subscriber['lat'],
                    subscriber['lon']
                ]
                
                # Add to sheet
                sheet.append_row(row_data)
                
                # Progress indicator
                print(f"✅ Added: {subscriber['name']} ({subscriber['email']}) - {subscriber['city']}, {subscriber['country']}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Failed to add {subscriber['name']}: {e}")
                continue
        
        # Read back to verify
        print(f"\n📖 Verifying data...")
        try:
            all_records = sheet.get_all_records()
            print(f"📊 Total records in sheet: {len(all_records)}")
            
            # Show sample of added data
            print(f"\n📋 Sample of added subscribers:")
            for i, record in enumerate(all_records[:5], 1):
                print(f"{i}. {record['Name']} - {record['Email']} - {record['City']}, {record['Country']}")
            
            print(f"\n🎉 Successfully populated Google Sheet with dummy subscribers!")
            print(f"🌍 Data includes subscribers from multiple countries and regions")
            print(f"📅 Timestamps span the last 30 days")
            print(f" View your sheet at: {spreadsheet.url}")
            
        except Exception as e:
            print(f"❌ Error reading back data: {e}")
        
    except Exception as e:
        print(f"❌ Error populating dummy data: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if google-credentials.json exists in project root")
        print("2. Verify Google Sheets API is enabled")
        print("3. Ensure the service account has access to the sheet")

if __name__ == '__main__':
    populate_dummy_data()