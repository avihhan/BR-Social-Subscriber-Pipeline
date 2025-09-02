'''
This script is used to setup the Google Sheets with proper headers

Usage:
python setup_google_sheets.py
'''


import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

def setup_google_sheets():
    """Setup Google Sheets with proper headers"""
    
    # Define the scope
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        # Load credentials
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'google-credentials.json', SCOPES)
        client = gspread.authorize(credentials)
        
        # Create or open the spreadsheet
        spreadsheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Subscriber List')
        
        try:
            spreadsheet = client.open(spreadsheet_name)
            print(f"Opened existing spreadsheet: {spreadsheet_name}")
        except gspread.SpreadsheetNotFound:
            spreadsheet = client.create(spreadsheet_name)
            print(f"Created new spreadsheet: {spreadsheet_name}")
        
        # Get the first sheet
        sheet = spreadsheet.sheet1
        
        # Set headers
        headers = [
            'Name', 'Email', 'Timestamp', 'IP Address', 
            'Country', 'Region', 'City', 'Latitude', 'Longitude'
        ]
        
        # Clear existing content and set headers
        sheet.clear()
        sheet.append_row(headers)
        
        # Format headers (make them bold)
        sheet.format('A1:I1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
        })
        
        print("Google Sheets setup completed successfully!")
        print(f"Spreadsheet URL: {spreadsheet.url}")
        
    except Exception as e:
        print(f"Error setting up Google Sheets: {e}")
        print("Make sure you have:")
        print("1. google-credentials.json file in the project root")
        print("2. Proper Google Cloud Project setup")
        print("3. Google Sheets API enabled")

if __name__ == '__main__':
    setup_google_sheets()