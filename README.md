# Subscriber Pipeline (Flask + Google Sheets + SMTP + Google Drive Templates)

A modern emailing pipeline to collect subscribers into Google Sheets, automatically send welcome emails, and send HTML email campaigns using templates stored in Google Drive.

## Features
- **Google Sheets as the subscriber database** - Store subscriber data with automatic IP geolocation
- **Automatic welcome emails** - New subscribers receive personalized welcome emails immediately
- **Google Drive template storage** - HTML templates stored in Google Drive for easy management
- **Flexible subscription** - Name field is optional (defaults to "Anonymous")
- **Smart duplicate detection** - Prevents duplicate subscriptions with case-insensitive email matching
- **IP geolocation** - Automatically captures country, region, city, latitude, longitude
- **Unsubscribe management** - Easy removal of subscribers by email
- **Data normalization** - All string fields stored in lowercase for consistency

---

## 1) Prerequisites
- Python 3.10/3.11 recommended
- A Google Cloud project with Google Sheets API and Google Drive API enabled
- A Google Service Account and credentials JSON file
- SMTP account (e.g., Gmail with App Password)

---

## 2) Google Cloud & Sheets Setup
1. Create/select a project in Google Cloud Console.
2. Enable APIs:
   - Google Sheets API
   - Google Drive API
   - Google Drive API v3
3. Create a Service Account and download its key JSON file. Save it in the project root as:
   - `google-credentials.json`
4. Create a Google Sheet named (default):
   - `Subscriber List`
5. Share the sheet with your service account email (Editor access).
6. **Set up Google Drive folder for templates**:
   - Create a folder called "Html Templates" in your Google Drive
   - Upload your HTML template files (e.g., `subscribed.html`, `intro.html`, `newsletter.html`)
   - Share the "Html Templates" folder with your service account email (Viewer access)

Optional: Run the helper to set up headers (or create them manually):
- The sheet should include headers in the first row:
  - `Name | Email | Timestamp | IP Address | Country | Region | City | Latitude | Longitude`

---

## 3) Local Configuration
Create a `.env` file in the project root:

```
# Google Sheets
GOOGLE_SHEET_NAME=Subscriber List

# SMTP (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=BullRunAI
```

Notes:
- For Gmail, enable 2FA and create an App Password.
- `GOOGLE_SHEET_NAME` can be changed to point to a different sheet.

---

## 4) Install & Run
Install dependencies:
```
pip install -r requirements.txt
```
Run the server:
```
python main.py
```
The API listens on `http://localhost:8000`.

**Note**: The project now uses `main.py` instead of `app.py` for better Cloud Functions compatibility.

---

## 5) Email Templates
**Templates are now stored in Google Drive** for easy management and updates without redeployment.

### Template Setup:
1. **Google Drive Folder**: Create a folder called "Html Templates" in your Google Drive
2. **Required Templates**:
   - `subscribed.html` - Welcome email sent automatically to new subscribers
   - `intro.html` - General email template for campaigns
   - `newsletter.html` - Newsletter template
3. **Template Features**:
   - Use `{{name}}` placeholder for subscriber personalization
   - Support for HTML, CSS, and embedded images
   - Easy to update without redeploying the function

### Template Examples:
- **subscribed.html**: Welcome message with `{{name}}` placeholder
- **intro.html**: Campaign template with customizable content
- **newsletter.html**: Newsletter format with branding

### Images in Emails:
- Most email clients block relative paths. Use absolute HTTPS URLs, or embed via CID attachments
- If using local images (e.g., `images/bullrun.png`, `images/page.png`), host them on a CDN and replace `src` with the CDN URL in your template

---

## 6) API Endpoints
All responses are JSON.

### Health
- GET `/health`
- Returns service status.
```
curl -s http://localhost:8000/health
```

### Subscribe
- POST `/subscribe`
- Body (JSON):
```
{
  "name": "avi kumar",  // Optional - defaults to "Anonymous" if not provided
  "email": "avihhan.official@gmail.com"
}
```
- **NEW**: Name field is now optional! If not provided, it defaults to "Anonymous"
- **NEW**: Automatic welcome email sent using `subscribed.html` template from Google Drive
- Behavior:
  - Detects client IP (or uses `X-Forwarded-For` if present)
  - Geolocates rough `country/region/city` (IP-API)
  - Lowercases string fields and appends a row to Google Sheet
  - **Automatically sends personalized welcome email** using `subscribed.html` template
  - Duplicate emails are detected (case-insensitive) using the Email column; returns existing record if already subscribed
- Examples:
```
# Subscribe with name
curl -s -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{"name":"avi kumar","email":"avihhan.official@gmail.com"}'

# Subscribe without name (will use "Anonymous")
curl -s -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email":"anonymous@example.com"}'
```
- On duplicate:
```
{
  "message": "already subscribed",
  "data": { "name": "avi kumar", "email": "avihhan.official@gmail.com", "timestamp": "2025-09-01 12:34:56" }
}
```
- On success (with welcome email sent):
```
{
  "message": "Subscriber added successfully",
  "data": { "name": "avi kumar", "email": "avihhan.official@gmail.com", "timestamp": "2025-09-01 12:34:56", "ip_address": "192.168.1.1", "location": {...} }
}
```

### List Subscribers
- GET `/subscribers`
- Optional query params: `start_date`, `end_date`, `country`, `region`, `city`
- Examples:
```
# All
curl -s "http://localhost:8000/subscribers"

# Date range + country
curl -s "http://localhost:8000/subscribers?start_date=2024-01-01&end_date=2025-12-31&country=united%20states"
```

### Send Template Email Campaign
- POST `/send-template-email`
- Body (JSON):
```
{
  "template_name": "intro",    
  "subject": "BullRunAI Launch",
  "advertisement_html": "<p>Special offer: Get 20% off!</p>"  // Optional
}
```
- **NEW**: Templates are now loaded from Google Drive "Html Templates" folder
- Uses `{template_name}.html` from Google Drive per subscriber with placeholders like `{{name}}`
- Sends personalized HTML emails via SMTP
- **No need to redeploy** when updating templates - just update files in Google Drive
- Example:
```
curl -s -X POST http://localhost:8000/send-template-email \
  -H "Content-Type: application/json" \
  -d '{"template_name":"intro","subject":"BullRunAI Launch","advertisement_html":"<p>Special offer: Get 20% off!</p>"}'
```

### Unsubscribe
- POST `/unsubscribe`
- Body (JSON):
```
{ "email": "user@example.com" }
```
- Deletes matching row from the sheet (case-insensitive match on Email column).
- Example:
```
curl -s -X POST http://localhost:8000/unsubscribe \
  -H "Content-Type: application/json" \
  -d '{"email":"avihhan.official@gmail.com"}'
```

---

## 7) Seeding (Optional)
Populate the sheet with dummy data:
```
python seed/populate_dummy_data.py
```
Notes:
- Script expects `google-credentials.json` in the project root and the sheet shared with the service account.
- Writes all string fields in lowercase.
- **NEW**: All string data (name, email, IP, location) is normalized to lowercase for consistency.

---

## 8) Troubleshooting
- **Credentials**:
  - Ensure `google-credentials.json` is present and the sheet is shared with the service account
  - Make sure the "Html Templates" folder in Google Drive is shared with your service account
- **Quota errors**:
  - Free Google Drive/Sheets quotas may be exceeded. Free up space or use an existing sheet
- **Emails delivered as plain text**:
  - Ensure your SMTP credentials are correct and the app is using HTML path
  - Avoid emojis or ensure UTF-8 subjects/bodies
- **Images not visible in email**:
  - Use absolute URLs (CDN) or embed images as CID attachments
- **Welcome emails not sending**:
  - Check that `subscribed.html` exists in your Google Drive "Html Templates" folder
  - Verify the folder is shared with your service account
  - Check function logs for detailed error messages
- **Template loading errors**:
  - Ensure the "Html Templates" folder name is exactly as specified
  - Check that template files have `.html` extension
  - Verify Google Drive API permissions

---

## 9) Security & Production Notes
- Do not commit `google-credentials.json` or `.env` to version control
- Use an environment-specific `.env` loader or secret manager in production
- Put the Flask app behind a proper WSGI server (gunicorn/uwsgi) and reverse proxy (nginx)
- **Google Drive templates**: Ensure proper sharing permissions for the "Html Templates" folder
- **Service account security**: Use least-privilege access for your service account

---

## 10) Project Structure
```
Subscriber Pipeline/
├─ main.py              # Main application (Cloud Functions compatible)
├─ requirements.txt     # Dependencies including Google Drive API
├─ .env                 # Your local environment variables
├─ google-credentials.json
├─ templates/           # Local templates (legacy - now using Google Drive)
│  └─ intro.html
├─ images/
│  ├─ bullrun.png
│  └─ page.png
└─ seed/
   └─ populate_dummy_data.py
```

**Note**: Templates are now primarily stored in Google Drive "Html Templates" folder for easier management.

---

## 11) Cloud Functions Deployment

### Deploy to Google Cloud Functions:
```bash
# Deploy the function
gcloud functions deploy subscriber-pipeline \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point subscriber_pipeline \
  --source . \
  --region us-central1 \
  --memory 512MB \
  --timeout 540s \
  --project brsocial
```

### Set Environment Variables:
```bash
# Set Google Sheet name
gcloud functions deploy subscriber-pipeline \
  --update-env-vars GOOGLE_SHEET_NAME="Subscriber List" \
  --region us-central1 \
  --project brsocial

# Set SMTP configuration
gcloud functions deploy subscriber-pipeline \
  --update-env-vars SMTP_SERVER=smtp.gmail.com,SMTP_PORT=587,FROM_NAME="Subscriber Pipeline" \
  --region us-central1 \
  --project brsocial

# Set SMTP credentials
gcloud functions deploy subscriber-pipeline \
  --update-env-vars SMTP_USERNAME="your-email@gmail.com",SMTP_PASSWORD="your-app-password",FROM_EMAIL="your-email@gmail.com" \
  --region us-central1 \
  --project brsocial
```

### Test Deployed Function:
```bash
# Test health endpoint
curl -X GET "https://us-central1-brsocial.cloudfunctions.net/subscriber-pipeline/health"

# Test subscribe (will send welcome email automatically)
curl -X POST "https://us-central1-brsocial.cloudfunctions.net/subscriber-pipeline/subscribe" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

---

## License
MIT (c) BullRunAI
